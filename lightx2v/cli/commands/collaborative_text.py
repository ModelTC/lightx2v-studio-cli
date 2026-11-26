"""Peer text editing over the existing immutable operation journal."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode, quote
import uuid
from .public_workflow import atomic_json, project_file, mutate, json_arg, journal


def add_text_commands(nested,handler):
    group=nested.add_parser('text',help='Collaboratively read or edit a node prompt/document').add_subparsers(dest='text_command',required=True)
    for action in ('get','edit'):
        parser=group.add_parser(action)
        parser.add_argument('node_id');parser.add_argument('--canvas-id','--workflow-id',dest='target_workflow',metavar='CANVAS_ID')
        parser.add_argument('--kind',choices=['prompt','document'],default='prompt')
        parser.add_argument('--port-id',default='in-text')
        parser.add_argument('--json',action='store_true');parser.add_argument('--quiet',action='store_true')
        if action=='edit':parser.add_argument('--input',required=True);parser.add_argument('--operation-id')
        parser.set_defaults(handler=handler,public_operation='text-'+action)


def handle_text(client,doctor,args,wid):
    identity=[client.config.base_url.rstrip('/'),doctor['user_id'],wid,args.node_id,args.kind,args.port_id]
    suffix=hashlib.sha256(json.dumps(identity).encode()).hexdigest()
    cache=project_file().parent/'text-contexts'/(suffix+'.json')
    instance=project_file().parent/'text-client.json'
    if not instance.exists():
        try:atomic_json(instance,{'client_id':'canvas-cli:'+uuid.uuid4().hex},exclusive=True)
        except FileExistsError:pass
    cid=json.loads(instance.read_text())['client_id']
    base=f'/api/v1/workflow/{quote(wid,safe="")}/collaborative_text'
    read_path=base+'/'+quote(args.node_id,safe='')+'?'+urlencode({'kind':args.kind,'port_id':args.port_id})
    def read():
        value=client._request('GET',read_path)
        atomic_json(cache,{'identity':identity,**value['text']})
        return value['text']
    if args.public_operation=='text-get':
        record=read()
        return {'source':record['source'],'epoch':record['epoch'],'context_file':str(cache),'raw_source':record.get('raw_source',False)}
    intent=json_arg(args.input)
    if set(intent)-{'source','append','edits'} or sum(key in intent for key in ('source','append','edits'))!=1:
        raise ValueError('Supply exactly one of source, append, or edits')
    oid=getattr(args,'operation_id',None)
    previous_path=journal(client.config,doctor,wid,'text',oid) if oid else None
    previous=json.loads(previous_path.read_text()) if previous_path and previous_path.is_file() else None
    if previous:
        body=previous['body']
        if body.get('text_intent')!=intent:raise ValueError('Operation ID already has a different saved text intent')
    else:
        record=json.loads(cache.read_text()) if cache.is_file() else read()
        if record.get('identity',identity)!=identity:raise ValueError('Text context belongs to another target')
        if record.get('raw_source'):raise ValueError('This document requires exclusive Markdown source editing; use its source editor before causal text editing')
        source=record['source']
        if 'source' in intent:source=intent['source']
        elif 'append' in intent:
            if not isinstance(intent['append'],str):raise ValueError('append must be a string')
            source+=intent['append']
        else:
            if not isinstance(intent['edits'],list) or not intent['edits']:raise ValueError('edits must be a nonempty list')
            for edit in intent['edits']:
                old,new=edit.get('old'),edit.get('new')
                if not isinstance(old,str) or not old or not isinstance(new,str) or source.count(old)!=1:raise ValueError('Text anchor is missing or ambiguous; read the latest text')
                source=source.replace(old,new,1)
        if not isinstance(source,str):raise ValueError('Text must be a string')
        body={'node_id':args.node_id,'kind':args.kind,'port_id':args.port_id,'client_id':cid,
            'action':'replace','source':source,'epoch':record['epoch'],'base_state':record['state'],
            'edit_origin':{'kind':'cli','session_id':cid,'intent':'manual'},'text_intent':intent}
    def send(payload):
        return client._request('POST',base,json={**payload,'mutation_id':payload['operation_id']})
    result=mutate(client,doctor,args,wid,'text',body,send,version=False)
    record=read()
    if args.kind=='document':
        # Body edits are durable already. Publish the existing immutable document
        # checkpoint too, so downloads and non-browser runs observe this edit.
        checkpoint_id='text-checkpoint:'+hashlib.sha256((str(result.get('operation_id'))+record['epoch']+record.get('vector','')).encode()).hexdigest()[:64]
        checkpoint={key:value for key,value in body.items() if key in {'node_id','kind','port_id','client_id','edit_origin'}}
        checkpoint.update(action='checkpoint',epoch=record['epoch'],vector=record.get('vector'),operation_id=checkpoint_id)
        from types import SimpleNamespace
        mutate(client,doctor,SimpleNamespace(operation_id=checkpoint_id),wid,'text',checkpoint,send,version=False)
        record=read()
    return {**{key:value for key,value in result.items() if key!='text'},'text':{'source':record['source'],'epoch':record['epoch']},'context_file':str(cache)}
