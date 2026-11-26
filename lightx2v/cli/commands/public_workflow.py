"""Public Canvas commands. Domain schemas, authorization and execution stay remote."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.parse import urljoin, urlsplit
import uuid
import zipfile

import httpx

from lightx2v.cli.client import ApiError, LightX2VClient
from lightx2v.cli.config import resolve_config, ConfigError
from lightx2v.cli.json_util import load_json_arg

PROTOCOL = 'public-canvas-v1'


class CommandFailure(Exception):
    def __init__(self, code, message):self.code, self.message = code, message


def output(value):
    print(json.dumps(value, ensure_ascii=False, allow_nan=False))


def project_file():
    for root in [Path.cwd(), *Path.cwd().parents]:
        path = root / '.lightx2v' / 'project.json'
        if path.is_file():return path
    return Path.cwd() / '.lightx2v' / 'project.json'


def atomic_json(path, value, *, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush();os.fsync(stream.fileno())
        if exclusive:
            publish_file(Path(name), path)
        else:
            os.replace(name, path)
    finally:
        if os.path.exists(name):os.unlink(name)


def publish_file(source, destination):
    # Atomic create-if-absent; a concurrent download must not overwrite it.
    os.link(source, destination)
    os.unlink(source)


def workflow_id(args, config, doctor):
    explicit = getattr(args, 'workflow_id', None) or getattr(args, 'target_workflow', None)
    if getattr(args, 'workflow_id', None) and getattr(args, 'target_workflow', None) and args.workflow_id != args.target_workflow:
        raise ValueError('Conflicting workflow IDs')
    if explicit:return explicit
    path = project_file()
    if not path.is_file():raise ValueError('Specify a workflow ID or run workflow use first')
    record = json.loads(path.read_text())
    if record.get('base_url') != config.base_url.rstrip('/') or record.get('user_id') != doctor['user_id']:
        raise ValueError('Project context belongs to another service/account; run workflow use explicitly')
    return record['workflow_id']


def json_arg(value, default=None):
    result = load_json_arg(value) if value else (default if default is not None else {})
    if not isinstance(result, dict):raise ValueError('Expected a JSON object')
    return result


def api_path(wid, tail):
    if not isinstance(wid, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', wid):raise ValueError('Invalid workflow ID')
    return f'/api/v1/workflow/{wid}/public/{tail}'


def journal(config, doctor, wid, kind, oid):
    identity = json.dumps([config.base_url.rstrip('/'), doctor['user_id'], wid, kind, oid])
    return project_file().parent / 'operations' / (hashlib.sha256(identity.encode()).hexdigest() + '.json')


def mutate(client, doctor, args, wid, kind, body, sender, *, version=True):
    if getattr(args,'operation_id',None) and body.get('operation_id') not in (None,args.operation_id):
        raise ValueError('Conflicting operation IDs')
    if getattr(args,'version',None) is not None and body.get('version') not in (None,args.version):
        raise ValueError('Conflicting versions')
    oid=getattr(args,'operation_id',None) or body.get('operation_id') or uuid.uuid4().hex
    body={**body,'operation_id':oid}
    path=journal(client.config,doctor,wid,kind,oid)
    path.parent.mkdir(parents=True,exist_ok=True)
    # One immutable local request per operation, even with two CLI processes.
    with path.with_suffix('.lock').open('a+b') as lock:
        if os.name=='nt':
            import msvcrt
            lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX)
        try:
            return _mutate_locked(client,doctor,args,wid,kind,body,sender,version=version)
        finally:
            if os.name=='nt':
                lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(lock,fcntl.LOCK_UN)


def _mutate_locked(client, doctor, args, wid, kind, body, sender, *, version=True):
    oid = getattr(args, 'operation_id', None) or body.get('operation_id') or uuid.uuid4().hex
    if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,96}', oid):raise ValueError('Invalid operation ID')
    if body.get('operation_id') not in (None, oid):raise ValueError('Conflicting operation IDs')
    body = {**body, 'operation_id': oid}
    path = journal(client.config, doctor, wid, kind, oid)
    supplied_version = getattr(args, 'version', None)
    if supplied_version is None:supplied_version=body.get('version')
    if supplied_version is not None and (type(supplied_version) is not int or supplied_version<1):raise ValueError('Version must be a positive integer')
    previous = json.loads(path.read_text()) if path.is_file() else None
    if version:
        if supplied_version is None and previous:
            body['version'] = previous['body']['version']
        else:
            body['version'] = supplied_version or client.get_workflow(wid)['version']
    if previous and previous['body'] != body:raise ValueError('Operation ID already has a different saved request')
    record = previous or {'protocol':PROTOCOL, 'base_url':client.config.base_url.rstrip('/'),
        'user_id':doctor['user_id'], 'workflow_id':wid, 'kind':kind, 'operation_id':oid, 'body':body}
    record['status']='sending'
    atomic_json(path, record)
    print(json.dumps({'operation_id':oid, 'recovery_file':str(path)}), file=sys.stderr, flush=True)
    try:
        result = sender(body)
    except (httpx.TransportError, KeyboardInterrupt) as error:
        record['status']='unknown';atomic_json(path,record)
        raise CommandFailure(4, {'code':'outcome_unknown','operation_id':oid,'kind':kind,
            'workflow_id':wid,'recovery_file':str(path),'hint':'Query the original operation or repeat this exact request; do not use a new ID'}) from error
    except ApiError as error:
        payload = getattr(error, 'payload', {}) or {}
        detail=payload.get('detail') if isinstance(payload.get('detail'),dict) else {}
        code=payload.get('code') or detail.get('code')
        explicit = payload.get("outcome_unknown")
        unknown = explicit if isinstance(explicit, bool) else (error.status_code >= 500 and code not in {"public_canvas_disabled", "canvas_access_denied"})
        record['status']='unknown' if unknown else 'rejected';atomic_json(path,record)
        if unknown:raise CommandFailure(4, {'code':'outcome_unknown','operation_id':oid,'kind':kind,'workflow_id':wid}) from error
        raise
    record.update(status='returned',result=result);atomic_json(path,record)
    return result


def edit_item(args):
    item = json_arg(getattr(args,'input',None))
    action = args.public_action
    item.update(item_id='item',action=action)
    for attr, key in [('node_id','node_id'),('name','name'),('tool_id','tool_id'),('group_id','group_id'),
                      ('source_node_id','source_node_id'),('target_node_id','target_node_id'),
                      ('source_port','source_port_id'),('target_port','target_port_id'),('connection_id','connection_id')]:
        value=getattr(args,attr,None)
        if value is not None:item[key]=value
    for attr, key in [('parameters','parameters'),('text_inputs','text_inputs')]:
        if getattr(args,attr,None):item[key]=json_arg(getattr(args,attr))
    if getattr(args,'body',None) is not None:item['body']=args.body
    if getattr(args,'body_file',None):item['body']=Path(args.body_file).read_text(encoding='utf-8')
    position={k:getattr(args,k) for k in ('x','y','width','height') if getattr(args,k,None) is not None}
    if position:item['position']=position
    if getattr(args,'node_ids',None):item['node_ids']=args.node_ids
    if getattr(args,'input_ids',None):item['input_ids']=args.input_ids
    if getattr(args,'target_port',None) and action=='reorder_inputs':
        item.pop('target_port_id',None);item['target_port_id']=args.target_port
    if getattr(args,'color',None):item['color']=args.color
    if action=='group_set_parent':
        item['expected_parent_group_id']=getattr(args,'expected_parent_group_id',None)
        item['parent_group_id']=None if args.root else args.parent_group_id
    if action=='group_move_members':
        item['source_group_id']=item.pop('group_id')
        item['target_group_id']=args.target_group_id
    if action=='copy':item['node_ids']=[item.pop('node_id')]
    return item


def edit_items(args):
    item = edit_item(args)
    if item['action'] != 'update':
        return [item]
    # The remote typed contract separates parameter edits, document revisions,
    # and layout. Keep one atomic batch rather than sending invalid update keys.
    body = item.pop('body', None)
    has_body = getattr(args, 'body', None) is not None or bool(getattr(args, 'body_file', None))
    supplied = json_arg(getattr(args, 'input', None))
    has_body = has_body or 'body' in supplied
    position = item.pop('position', None)
    parts = [item] if set(item) - {'item_id', 'action', 'node_id'} else []
    if has_body:
        parts.append({'item_id':'item-body' if parts else 'item','action':'body',
                      'node_id':item['node_id'],'body':body})
    if position is not None:
        parts.append({'item_id':'item-move' if parts else 'item','action':'move',
                      'node_id':item['node_id'],'position':position})
    return parts or [item]


def read_script(client, wid, args):
    path = api_path(wid, 'script/read')
    body = {
        key: getattr(args, key)
        for key in ('node_id', 'revision', 'section', 'view', 'ids', 'offset', 'limit')
        if getattr(args, key) is not None
    }
    try:
        return client._request('POST', path, json=body)
    except ApiError as error:
        missing_route = {404: {'detail': 'Not Found'}, 405: {'detail': 'Method Not Allowed'}}
        if (args.view != 'detail' or error.status_code not in missing_route
                or error.payload != missing_route[error.status_code]):
            raise
    print('Using the legacy Script detail endpoint.', file=sys.stderr)
    body.pop('view')
    body.setdefault('limit', 5)
    body['action'] = 'read'
    return client._request('POST', f'/api/v1/workflow/{wid}/script', json=body)


def handle(args):
    try:
        if getattr(args, 'payload_only', False) and not getattr(args, 'case', None):
            raise ValueError('--payload-only requires --case')
        config=resolve_config()
        with LightX2VClient(config,notify_updates=False) as client:
            try:
                doctor=client._request('GET','/api/v1/workflow/public/doctor')
            except ApiError as error:
                if error.status_code in {404,405}:
                    raise CommandFailure(1, {'code':'public_canvas_protocol_unavailable',
                        'message':'Server does not support public-canvas-v1; upgrade the server'}) from error
                raise
            if doctor.get('protocol') != PROTOCOL:raise ValueError('Server does not support public-canvas-v1; upgrade the server')
            op=args.public_operation
            if op=='doctor':output(doctor);return 0
            if not doctor.get('account_allowed'):raise CommandFailure(1,{'code':'canvas_access_denied'})
            if op == 'script-guide':
                body = {'view': args.script_command}
                for key in ('section', 'field', 'case', 'topic', 'action'):
                    if getattr(args, key, None) is not None:
                        body[key] = getattr(args, key)
                try:
                    result = client._request('POST', '/api/v1/workflow/public/script/guide', json=body)
                except ApiError as error:
                    if error.status_code in {404, 405} and error.payload in ({'detail': 'Not Found'}, {'detail': 'Method Not Allowed'}):
                        raise CommandFailure(1, {'code': 'script_contract_unavailable',
                            'message': 'Server lacks Script field discovery; upgrade the server. Do not infer fields from an outdated skill.'}) from error
                    raise
                if getattr(args, 'payload_only', False):
                    result = result['payload']
            elif op=='create':
                body={'name':args.name or '未命名画布','description':args.description or ''}
                result=mutate(client,doctor,args,'new','create',body,
                    lambda body:client._request('POST','/api/v1/workflow/public/create',json=body),version=False)
            elif op=='operation' and args.kind=='create':
                result=client._request('GET','/api/v1/workflow/public/operations/'+args.operation)
            else:
                wid=workflow_id(args,config,doctor)
                if op in ('text-get','text-edit'):
                    from .collaborative_text import handle_text
                    result=handle_text(client,doctor,args,wid)
                elif op=='use':
                    client.get_workflow(wid)
                    result={'base_url':config.base_url.rstrip('/'),'user_id':doctor['user_id'],'workflow_id':wid}
                    atomic_json(project_file(),result)
                elif op=='capabilities':
                    body=json_arg(args.input)
                    if args.tool_id:body['queries']=[{'tool_id':args.tool_id}]
                    result=client._request('POST',api_path(wid,'capabilities'),json=body)
                elif op == 'script-read':
                    result = read_script(client, wid, args)
                elif op == 'script-stage':
                    path = api_path(wid, 'script/' + args.script_command)
                    body = json_arg(args.input)
                    if args.script_command in {'preview', 'prompts'}:
                        result = client._request('POST', path, json=body)
                    else:
                        result = mutate(client, doctor, args, wid, 'sync' if args.script_command == 'sync-anchors' else 'edit', body,
                                        lambda request: client._request('POST', path, json=request),
                                        version=False)
                elif op in ('nodes','node-get'):
                    body=json_arg(args.input)
                    if op=='node-get':body.update(node_ids=[args.node_id],include=args.include or ['configuration'])
                    else:
                        for attr,key in [('query','query'),('category','category'),('group_id','group_id'),('limit','limit'),('cursor','cursor')]:
                            if getattr(args,attr,None) is not None:body[key]=getattr(args,attr)
                    result=client._request('POST',api_path(wid,'nodes'),json=body)
                elif op in ('group-list','group-get'):
                    result=client._request('POST',api_path(wid,'nodes'),json={'view':'groups' if op=='group-list' else 'group_members',**({'group_id':args.group_id} if op=='group-get' else {})})
                elif op in ('edit','item','rename'):
                    if op=='edit':body=json_arg(args.input)
                    elif op=='rename':body={'items':[{'item_id':'rename','action':'metadata','name':args.name}]}
                    else:body={'items':edit_items(args)}
                    result=mutate(client,doctor,args,wid,'edit',body,lambda body:client._request('POST',api_path(wid,'edit'),json=body))
                elif op=='delete':
                    result=mutate(client,doctor,args,wid,'delete',{},lambda body:client._request('DELETE',f'/api/v1/workflow/{wid}/public',json=body),version=False)
                elif op=='operation' and args.kind=='text':
                    from urllib.parse import quote
                    saved=journal(config,doctor,wid,'text',args.operation)
                    if not saved.is_file():raise ValueError('Text operation identity is not available in this project')
                    record=json.loads(saved.read_text())
                    result=client._request('GET',f'/api/v1/workflow/{quote(wid,safe="")}/edit_receipts/{quote(args.operation,safe="")}',params={'client_id':record['body']['client_id']})
                elif op=='operation':
                    result=client._request('GET',api_path(wid,'operations/'+args.operation),params={'kind':args.kind})
                elif op in ('run','quote'):
                    from .workflow import _run_body
                    body=_run_body(args)
                    if args.node_ids and args.mode=='full':
                        raise ValueError('--node-id requires --mode single, downstream or upstream; full runs the entire workflow')
                    if args.group_id:
                        if args.node_ids:raise ValueError('Do not combine group and node scopes')
                        body.update(group_id=args.group_id,mode='single')
                    if op=='quote':
                        body.pop('save_as_default',None)
                        result=client._request('POST',api_path(wid,'quote'),json=body)
                    else:
                        result=mutate(client,doctor,args,wid,'run',body,lambda body:client._request('POST',api_path(wid,'runs'),json=body),version=False)
                        if args.poll:return wait(client,wid,result['run_id'],args.timeout,args.poll_interval,'terminal')
                elif op=='wait':return wait(client,wid,args.run_id,args.timeout,args.poll_interval,args.until)
                elif op=='upload':
                    path=Path(args.file).expanduser().resolve()
                    with path.open('rb') as source:
                        sha=hashlib.sha256()
                        for chunk in iter(lambda:source.read(1024*1024),b''):sha.update(chunk)
                    body={'sha256':sha.hexdigest(),'name':args.name or path.name}
                    if args.node_id:body['node_id']=args.node_id
                    if args.group_id:body['group_id']=args.group_id
                    position={k:getattr(args,k) for k in ('x','y') if getattr(args,k,None) is not None}
                    if position:body['position']=position
                    def send_upload(body):
                        import mimetypes
                        with path.open('rb') as source:
                            request=httpx.Request('POST',urljoin(client.config.base_url+'/',api_path(wid,'uploads')),
                                headers={'Authorization':'Bearer '+client.config.api_key},data={'arguments':json.dumps(body)},
                                files={'file':(path.name,source,mimetypes.guess_type(path.name)[0] or 'application/octet-stream')})
                            response=client._client.send(request)
                        if not response.is_success:raise client._parse_error(response)
                        return response.json()
                    result=mutate(client,doctor,args,wid,'upload',body,send_upload)
                elif op=='download':return download(client,wid,args)
                else:raise ValueError('Unsupported public command')
            if result.get('saved') is True and any(result.get(key) for key in
                                                   ('script_documents', 'script_generators', 'script_changes')):
                result = {key: value for key, value in result.items() if key not in {'patch', 'typed_intent_hash'}}
            output(result)
            if result.get('outcome_unknown'):return 4
            if result.get('saved') is False or result.get('ok') is False:return 1
            return 0
    except CommandFailure as error:output({'ok':False,**(error.message if isinstance(error.message,dict) else {'message':error.message})});return error.code
    except (ValueError,OSError,ConfigError) as error:output({'ok':False,'code':'invalid_arguments','message':str(error)});return 2
    except ApiError as error:
        payload=getattr(error,'payload',None)
        output({'ok':False,'http_status':error.status_code,'error':payload or error.message})
        return 1
    except httpx.TransportError:output({'ok':False,'code':'connection_unavailable'});return 1
    except KeyboardInterrupt:return 130


def wait(client,wid,rid,timeout,interval,until):
    if timeout<0 or interval<=0:raise ValueError('Invalid wait duration')
    deadline=time.monotonic()+timeout
    while True:
        row=client.get_workflow_run(wid,rid)
        status=str(row.get('status','')).lower()
        terminal=status in {'succeeded','failed','cancelled'}
        result={'workflow_id':wid,'run_id':rid,'status':status,'terminal':terminal}
        if terminal:
            if until=='outputs':
                manifest=client._request('POST',api_path(wid,f'runs/{rid}/export'),json={})
                result['outputs']=manifest
                ready=manifest.get('complete',False)
            else:ready=True
            if ready:
                output({**result,'wait':{'outcome':'satisfied','until':until}})
                return 0 if status=='succeeded' else 1
            if status!='succeeded':
                output({**result,'wait':{'outcome':'blocked','until':until}});return 1
        if time.monotonic()>=deadline:
            output({**result,'wait':{'outcome':'timeout','until':until}});return 3
        time.sleep(min(interval,max(0,deadline-time.monotonic())))


def safe_name(value):
    name=re.sub(r'[^\w.\-\u4e00-\u9fff]+','_',str(value)).strip('._')[:100]
    return name or 'output'


def fetch_file(client,path,destination):
    from lightx2v.cli.downloads import stream_original
    with destination.open('wb') as stream:
        return stream_original(client.config,path,stream)


def download(client,wid,args):
    selection={}
    if args.node_ids:selection['node_ids']=args.node_ids
    if args.group_id:selection['group_id']=args.group_id
    manifest=client._request('POST',api_path(wid,f'runs/{args.run_id}/export'),json=selection)
    root=Path(args.output).expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
    files=[];failures=list(manifest.get('failures') or [])
    # A run-specific manifest is written even when some items are unavailable.
    manifest_path=root/('manifest-'+safe_name(args.run_id)+'.json')
    if manifest_path.exists():raise ValueError('Manifest already exists; choose a new output directory')
    with tempfile.TemporaryDirectory(prefix='.lightx2v-',dir=root) as temporary:
        staging=Path(temporary)
        for index,item in enumerate(manifest.get('items') or [],1):
            name=f'{index:03d}-'+safe_name(item.get('title') or item.get('object_id'))
            ext=item.get('ext') or '.bin'
            if not re.fullmatch(r'\.[A-Za-z0-9]{1,10}',ext):ext='.bin'
            name+=ext
            try:
                target=staging/name
                info=fetch_file(client,item['download_path'],target)
                if item.get('sha256') and item['sha256']!=info['sha256']:raise ValueError('Checksum mismatch')
                if item.get('size') is not None and item['size']!=info['size']:raise ValueError('Size mismatch')
                files.append({**item,**info,'filename':name})
            except (ValueError,OSError,httpx.HTTPError) as error:
                failures.append({'ref':item.get('ref'),'reason':type(error).__name__})
        if len(files)==1 and not args.zip:
            name=files[0]['filename'];destination=root/name
            if destination.exists():raise ValueError('Output already exists')
            publish_file(staging/name,destination)
        elif files:
            destination=root/('outputs-'+safe_name(args.run_id)+'.zip')
            if destination.exists():raise ValueError('ZIP already exists')
            bundle=staging/'outputs.zip'
            with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                for item in files:archive.write(staging/item['filename'],item['filename'])
                archive.writestr('manifest.json',json.dumps({**manifest,'items':files,'failures':failures},ensure_ascii=False))
            publish_file(bundle,destination)
        result={**manifest,'items':files,'failures':failures,'complete':not failures,
                'manifest':str(manifest_path),**({'output':str(destination)} if files else {})}
        atomic_json(manifest_path,result,exclusive=True)
    output(result)
    return 0 if not failures else 1


def common(parser, *, workflow=True, mutation=False):
    if workflow:parser.add_argument('workflow_id',nargs='?');parser.add_argument('--workflow-id',dest='target_workflow')
    parser.add_argument('--json',action='store_true');parser.add_argument('--quiet',action='store_true')
    if mutation:parser.add_argument('--operation-id');parser.add_argument('--version',type=int)
    return parser


def extend(nested,create,run):
    from .collaborative_text import add_text_commands
    add_text_commands(nested,handle)
    script = nested.add_parser('script', help='Read and prepare structured Script records')
    script_commands = script.add_subparsers(dest='script_command', required=True)
    schema = common(script_commands.add_parser('schema', help='Query live field types, defaults, semantics and maintenance ownership; no workflow required'), workflow=False)
    choice = schema.add_mutually_exclusive_group()
    choice.add_argument('--section', choices=['script', 'shots', 'anchors', 'units'])
    choice.add_argument('--action', help='Read the exact public request schema for edit, prepare-anchors, sync-anchors, prompts or another advertised action')
    choice.add_argument('--field', help='Field path, e.g. anchors.variant_of or shots.dialogue.speaker_id')
    schema.set_defaults(handler=handle, public_operation='script-guide')
    example = common(script_commands.add_parser('examples', help='List complete server-backed save/preview examples; no generation'), workflow=False)
    example.add_argument('--case', help='Case from the example catalogue')
    example.add_argument('--payload-only', action='store_true', help='Emit only the JSON payload for --case; fill documented runtime values before submitting')
    example.set_defaults(handler=handle, public_operation='script-guide')
    guide = common(script_commands.add_parser('guide', help='Read workflow, anchor prompt authoring, variants, editing or preflight rules without a basic skill'), workflow=False)
    guide.add_argument('--topic', choices=['workflow', 'editing', 'variants', 'anchor-prompts', 'preflight'], default='workflow')
    guide.set_defaults(handler=handle, public_operation='script-guide')
    read = common(script_commands.add_parser('read', help='Read a Script summary or a page of detail'), workflow=False)
    read.add_argument('node_id')
    read.add_argument('--workflow-id', dest='target_workflow')
    read.add_argument('--revision', help='Pin an exact Script revision')
    read.add_argument('--section', choices=['shots', 'anchors', 'units', 'subjects', 'outputs', 'media_sources', 'production'])
    read.add_argument('--view', choices=['summary', 'detail'])
    read.add_argument('--id', action='append', dest='ids', help='Read one or more stable IDs within the section')
    read.add_argument('--offset', type=int)
    read.add_argument('--limit', type=int)
    read.set_defaults(handler=handle, public_operation='script-read')
    for name, description in (
        ('edit', 'Patch Script records by stable ID and expected_revision'),
        ('prepare-anchors', 'Save image/voice anchor generators without running them'),
        ('sync-anchors', 'Reconcile existing anchor results; reuse the operation ID for recovery'),
        ('prompts', 'Read options or compose candidates; optimize uses the full-reference video preset for generation_model'),
        ('select-output', 'Adopt an exact image/video output, or clear it with selection:null'),
        ('preview', 'Preview video nodes and their ordered anchor inputs'),
        ('create-group', 'Save a previewed video group without running it'),
    ):
        stage = common(script_commands.add_parser(name, help=description))
        example = {'preview': 'preview-video', 'edit': 'edit-record'}.get(name, name)
        input_help = f'JSON object or @file. Read workflow script examples --case {example}.'
        if name == 'prompts':
            input_help += ' Use mode=options to find generation_models. In mode=optimize pass an ID with preset_id as generation_model.'
        else:
            input_help += ' See workflow script guide --topic preflight.'
        stage.add_argument('--input', required=True, help=input_help)
        if name not in {'preview', 'prompts'}:
            stage.add_argument('--operation-id', help='Stable ID for retry and workflow operation get')
        stage.set_defaults(handler=handle, public_operation='script-stage')
    # Preserve legacy JSON create; --name creates an idempotent empty canvas.
    create.add_argument('--name');create.add_argument('--description');create.add_argument('--operation-id')
    run.add_argument('--operation-id');run.add_argument('--group-id')
    run.set_defaults(handler=handle,public_operation='run')
    p=common(nested.add_parser('use'));p.set_defaults(handler=handle,public_operation='use')
    p=common(nested.add_parser('capabilities'));p.add_argument('--tool-id');p.add_argument('--input');p.set_defaults(handler=handle,public_operation='capabilities')
    p=common(nested.add_parser('nodes'));p.add_argument('--query');p.add_argument('--category');p.add_argument('--group-id');p.add_argument('--limit',type=int,default=50);p.add_argument('--cursor');p.add_argument('--input');p.set_defaults(handler=handle,public_operation='nodes')
    p=common(nested.add_parser('edit'),mutation=True);p.add_argument('--input',required=True);p.set_defaults(handler=handle,public_operation='edit')
    p=common(nested.add_parser('rename'),mutation=True);p.add_argument('--name',required=True);p.set_defaults(handler=handle,public_operation='rename')
    p=common(nested.add_parser('delete'),mutation=True);p.set_defaults(handler=handle,public_operation='delete')
    p=common(nested.add_parser('upload'),mutation=True);p.add_argument('--file',required=True);p.add_argument('--name');p.add_argument('--node-id');p.add_argument('--group-id');p.add_argument('--x',type=float);p.add_argument('--y',type=float);p.set_defaults(handler=handle,public_operation='upload')
    p=common(nested.add_parser('wait'));p.add_argument('run_id');p.add_argument('--timeout',type=float,default=300);p.add_argument('--poll-interval',type=float,default=2);p.add_argument('--until',choices=['terminal','outputs'],default='terminal');p.set_defaults(handler=handle,public_operation='wait')
    p=common(nested.add_parser('download'));p.add_argument('--run-id',required=True);p.add_argument('--node-id',action='append',dest='node_ids');p.add_argument('--group-id');p.add_argument('-o','--output',default='.');p.add_argument('--zip',action='store_true');p.set_defaults(handler=handle,public_operation='download')
    p=common(nested.add_parser('quote'));p.add_argument('--mode',choices=['full','single','downstream','upstream'],default='full');p.add_argument('--node-id',action='append',dest='node_ids');p.add_argument('--group-id');p.add_argument('--inputs');p.add_argument('--input-file',action='append',default=[]);p.add_argument('--no-include-upstream',action='store_true');p.set_defaults(handler=handle,public_operation='quote',save_as_default=False)
    p=nested.add_parser('operation');sub=p.add_subparsers(dest='operation_command',required=True);p=common(sub.add_parser('get'));p.add_argument('operation');p.add_argument('--kind',choices=['edit','upload','run','create','text','sync'],default='edit');p.set_defaults(handler=handle,public_operation='operation')
    node=nested.add_parser('node').add_subparsers(dest='node_command',required=True)
    for name,action in [('create','create'),('update','update'),('move','move'),('copy','copy'),('delete','delete'),('get',None)]:
        p=common(node.add_parser(name),workflow=False,mutation=bool(action));p.add_argument('--workflow-id',dest='target_workflow')
        if name!='create':p.add_argument('node_id')
        if action:
            p.add_argument('--input');p.add_argument('--name');p.add_argument('--tool-id');p.add_argument('--parameters');p.add_argument('--text-inputs')
            body=p.add_mutually_exclusive_group();body.add_argument('--body');body.add_argument('--body-file')
            for key in ['x','y','width','height']:p.add_argument('--'+key,type=float)
            p.set_defaults(handler=handle,public_operation='item',public_action=action)
        else:p.add_argument('--input');p.add_argument('--include',action='append',choices=['configuration','inputs','content','runtime','outputs','layout','diagnostics']);p.set_defaults(handler=handle,public_operation='node-get')
    for name,action in [('connect','connect'),('disconnect','disconnect'),('reorder-inputs','reorder_inputs')]:
        p=common(nested.add_parser(name),workflow=False,mutation=True);p.add_argument('--workflow-id',dest='target_workflow');p.add_argument('--input')
        if action=='connect':p.add_argument('source_node_id');p.add_argument('target_node_id');p.add_argument('--source-port');p.add_argument('--target-port')
        elif action=='disconnect':p.add_argument('connection_id')
        else:p.add_argument('node_id');p.add_argument('--target-port',required=True);p.add_argument('--input-id',action='append',dest='input_ids',required=True)
        p.set_defaults(handler=handle,public_operation='item',public_action=action)
    group=nested.add_parser('group').add_subparsers(dest='group_command',required=True)
    for name,action in [('list',None),('get',None),('create','group'),('update','group'),('add','group_add_members'),('remove','group_remove_members'),('move','group_move_members'),('set-parent','group_set_parent'),('ungroup','ungroup'),('copy','copy_group')]:
        p=common(group.add_parser(name),workflow=False,mutation=bool(action));p.add_argument('--workflow-id',dest='target_workflow')
        if name not in {'create','list'}:p.add_argument('group_id')
        if action:
            p.add_argument('--input');p.add_argument('--name');p.add_argument('--color');p.add_argument('--node-id',action='append',dest='node_ids')
            if name=='move':p.add_argument('--target-group-id',required=True)
            if name=='set-parent':
                parent=p.add_mutually_exclusive_group(required=True);parent.add_argument('--root',action='store_true');parent.add_argument('--parent-group-id');p.add_argument('--expected-parent-group-id')
            p.set_defaults(handler=handle,public_operation='item',public_action=action)
        else:p.set_defaults(handler=handle,public_operation='group-list' if name=='list' else 'group-get')


def add_doctor(subparsers):
    p=common(subparsers.add_parser('doctor',help='Read account and public Canvas protocol readiness'),workflow=False)
    p.set_defaults(handler=handle,public_operation='doctor')
