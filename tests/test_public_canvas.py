import hashlib
import json
from pathlib import Path

import httpx
import pytest

from lightx2v.cli.client import LightX2VClient
from lightx2v.cli.config import CliConfig
from lightx2v.cli.main import main, build_parser
from lightx2v.cli.commands import public_workflow as public


@pytest.fixture
def transport(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('LIGHTX2V_BASE_URL','https://api.example.test')
    monkeypatch.setenv('LIGHTX2V_API_KEY','apikey_fixture')
    calls=[];state={'version':1,'lost':False,'bodies':{}}
    def handler(request):
        calls.append(request)
        assert request.headers['authorization']=='Bearer apikey_fixture'
        path=request.url.path
        if path.endswith('/doctor'):return httpx.Response(200,json={'protocol':public.PROTOCOL,'user_id':state.get('user','u'),'account_allowed':True,'enabled':True})
        if path=='/api/v1/workflow/w':return httpx.Response(200,json={'workflow_id':'w','version':state['version'],'user_id':'u'})
        if path.endswith('/public/script/guide') and state.get('guide_response') is not None:
            return httpx.Response(state.get('guide_status', 200), json=state['guide_response'])
        if path.endswith('/public/script/read') and state.get('script_http_error'):
            return httpx.Response(state.get('script_http_status', 404), json=state['script_http_error'])
        if path.endswith('/edit'):
            if state.get('mutation_error'):
                return httpx.Response(503, json=state['mutation_error'])
            body=json.loads(request.content);oid=body['operation_id']
            if oid in state['bodies']:assert state['bodies'][oid]==body
            else:state['bodies'][oid]=body
            state['version']=99
            if state['lost']:
                state['lost']=False
                raise httpx.ReadTimeout('simulated lost reply',request=request)
            return httpx.Response(200,json={'saved':True,'bound':True,'operation_id':oid,'version':99})
        if '/operations/' in path:return httpx.Response(200,json={'found':True,'saved':True})
        return httpx.Response(200,json={'ok':True,'body':json.loads(request.content) if request.content else None})
    real_client=LightX2VClient
    def client(config,**kwargs):
        c=real_client(config,**kwargs);c._client.close()
        c._client=httpx.Client(base_url=config.base_url,transport=httpx.MockTransport(handler),headers={'Authorization':'Bearer '+config.api_key})
        return c
    monkeypatch.setattr(public,'LightX2VClient',client)
    return calls,state


def last_json(capsys):
    return json.loads(capsys.readouterr().out.splitlines()[-1])


def test_command_surface_is_registered():
    parser=build_parser()
    cases=[['doctor'],['workflow','edit','w','--input','{}'],['workflow','upload','w','--file','x.png'],
           ['workflow','node','create','--workflow-id','w','--tool-id','text-document'],
           ['workflow','connect','a','b','--workflow-id','w'],['workflow','group','set-parent','g','--root'],
           ['workflow','operation','get','w','op'],['workflow','wait','w','run'],
           ['workflow','download','w','--run-id','run'],['workflow','quote','w']]
    for args in cases:assert callable(parser.parse_args(args).handler)


def test_context_account_and_host_are_bound(transport,capsys):
    calls,state=transport
    assert main(['workflow','use','w','--json'])==0
    record=json.loads(Path('.lightx2v/project.json').read_text())
    assert record['user_id']=='u' and 'apikey_fixture' not in json.dumps(record)
    assert main(['workflow','capabilities','--json'])==0
    state['user']='another'
    assert main(['workflow','nodes','--json'])==2
    assert last_json(capsys)['code']=='invalid_arguments'


def test_lost_edit_reply_recovers_original_version_and_never_rewrites_id(transport,capsys):
    calls,state=transport;state['lost']=True
    command=['workflow','node','create','--workflow-id','w','--tool-id','text-document','--body','Original','--operation-id','stable','--json']
    assert main(command)==4
    first=last_json(capsys)
    assert first['operation_id']=='stable' and first['code']=='outcome_unknown'
    assert main(command)==0
    assert last_json(capsys)['saved']
    writes=[json.loads(r.content) for r in calls if r.url.path.endswith('/edit')]
    assert len(writes)==2 and writes[0]==writes[1] and writes[0]['version']==1
    assert 'apikey_fixture' not in ''.join(p.read_text() for p in Path('.lightx2v/operations').glob('*.json'))
    different=command.copy();different[different.index('Original')]='Changed'
    assert main(different)==2
    assert len([r for r in calls if r.url.path.endswith('/edit')])==2


def test_typed_batch_preserves_explicit_id_and_version(transport,capsys):
    calls,state=transport
    body={'operation_id':'batch','version':7,'items':[{'item_id':'a','action':'create','tool_id':'text-document'}]}
    assert main(['workflow','edit','w','--input',json.dumps(body),'--json'])==0
    request=next(r for r in calls if r.url.path.endswith('/edit'))
    assert json.loads(request.content)==body


def test_wait_timeout_is_observation_and_does_not_cancel(transport,monkeypatch,capsys):
    client=public.LightX2VClient(CliConfig('https://api.example.test','apikey_fixture'))
    client.get_workflow_run=lambda *args:{'status':'running'}
    assert public.wait(client,'w','original',0,1,'terminal')==3
    result=last_json(capsys)
    assert result['run_id']=='original' and result['wait']['outcome']=='timeout'
    assert not any('/cancel' in r.url.path for r in transport[0])
    client.close()


def test_generated_operation_id_is_saved_before_effect(transport,monkeypatch,capsys):
    calls,state=transport
    assert main(['workflow','rename','w','--name','New','--json'])==0
    result=last_json(capsys)
    path=list(Path('.lightx2v/operations').glob('*.json'))[0]
    record=json.loads(path.read_text())
    assert result['operation_id']==record['operation_id']
    assert record['body']['items'][0]=={'item_id':'rename','action':'metadata','name':'New'}


def test_download_redirect_never_sends_key_to_cdn(tmp_path,monkeypatch):
    requests=[]
    def handler(request):
        requests.append(request)
        if request.url.host=='api.example.test':
            assert request.headers.get('authorization')=='Bearer apikey_fixture'
            return httpx.Response(307,headers={'Location':'https://cdn.example.test/object'})
        assert 'authorization' not in request.headers
        return httpx.Response(200,content=b'original bytes')
    real=httpx.Client
    monkeypatch.setattr(public.httpx,'Client',lambda **kwargs:real(transport=httpx.MockTransport(handler),**kwargs))
    client=type('Client',(),{'config':CliConfig('https://api.example.test','apikey_fixture')})()
    target=tmp_path/'out.bin'
    info=public.fetch_file(client,'/media/file',target)
    assert target.read_bytes()==b'original bytes'
    assert info['sha256']==hashlib.sha256(b'original bytes').hexdigest()
    assert len(requests)==2


def test_exclusive_publication_does_not_overwrite(tmp_path):
    source=tmp_path/'temporary';source.write_bytes(b'new')
    target=tmp_path/'delivery';target.write_bytes(b'original')
    with pytest.raises(FileExistsError):public.publish_file(source,target)
    assert target.read_bytes()==b'original' and source.read_bytes()==b'new'


def test_stream_rechecks_same_run_before_reconnect(monkeypatch,capsys):
    from types import SimpleNamespace
    from lightx2v.cli.commands import workflow
    events=[]
    class Client:
        streams=0
        def get_workflow_run(self,wid,rid):
            events.append(('status',wid,rid))
            return {'status':'succeeded' if self.streams==2 else 'running'}
        def stream_workflow_run(self,wid,rid):
            events.append(('stream',wid,rid));self.streams+=1
            if self.streams==1:raise httpx.ReadError('lost')
            yield {'event':'run_status','data':{'status':'succeeded'}}
    monkeypatch.setattr(workflow,'with_client',lambda args,fn:fn(Client(),args,None))
    monkeypatch.setattr(workflow.time,'sleep',lambda _:None)
    assert workflow.handle_stream(SimpleNamespace(workflow_id='w',run_id='original',json=True,quiet=True))==0
    assert all(e[1:]==('w','original') for e in events)
    assert [e[0] for e in events]==['status','stream','status','status','stream','status']


def test_partial_download_reports_nonzero_and_actual_checksums(tmp_path,monkeypatch,capsys):
    from types import SimpleNamespace
    manifest={'run_id':'r','items':[{'ref':'good','object_id':'a','download_path':'/good'},
                                  {'ref':'missing','object_id':'b','download_path':'/missing'}],'failures':[]}
    client=SimpleNamespace(_request=lambda *a,**k:manifest)
    def fetch(client,path,target):
        if path=='/missing':raise httpx.ReadError('unavailable')
        target.write_bytes(b'original')
        return {'sha256':hashlib.sha256(b'original').hexdigest(),'size':8}
    monkeypatch.setattr(public,'fetch_file',fetch)
    assert public.download(client,'w',SimpleNamespace(node_ids=None,group_id=None,run_id='r',output=tmp_path,zip=False))==1
    result=last_json(capsys)
    assert not result['complete'] and result['failures'][0]['ref']=='missing'
    assert result['items'][0]['sha256']==hashlib.sha256(b'original').hexdigest()
    assert Path(result['output']).read_bytes()==b'original'


def test_batch_identity_cannot_be_silently_replaced_by_flag(transport,capsys):
    body={'operation_id':'original','version':1,'items':[]}
    assert main(['workflow','edit','w','--input',json.dumps(body),'--operation-id','different','--json'])==2
    assert not any(r.url.path.endswith('/edit') for r in transport[0])


def test_missing_key_is_structured_parameter_error(monkeypatch,capsys):
    from lightx2v.cli.config import ConfigError
    monkeypatch.setattr(public,'resolve_config',lambda:(_ for _ in ()).throw(ConfigError('API key not configured')))
    assert main(['doctor','--json'])==2
    assert last_json(capsys)['code']=='invalid_arguments'


def test_node_update_document_body_and_name_are_one_valid_typed_batch(transport,capsys):
    assert main(['workflow','node','update','doc','--workflow-id','w','--name','Updated','--body','New markdown','--operation-id','body-change','--json'])==0
    body=json.loads(next(r for r in transport[0] if r.url.path.endswith('/edit')).content)
    assert body['items']==[
        {'item_id':'item','action':'update','node_id':'doc','name':'Updated'},
        {'item_id':'item-body','action':'body','node_id':'doc','body':'New markdown'}]


def test_node_update_explicit_empty_body_is_a_clear_not_an_omitted_update(transport,capsys):
    assert main(['workflow','node','update','doc','--workflow-id','w','--body','','--operation-id','clear-body','--json'])==0
    body=json.loads(next(r for r in transport[0] if r.url.path.endswith('/edit')).content)
    assert body['items']==[{'item_id':'item','action':'body','node_id':'doc','body':''}]


@pytest.mark.parametrize('command', ['run', 'quote'])
def test_node_scope_rejects_default_full_before_submission(transport, capsys, command):
    calls, state = transport
    assert main(['workflow', command, 'w', '--node-id', 'n', '--json']) == 2
    assert not any(r.url.path.endswith(('/runs', '/quote')) for r in calls)
    assert '--mode single' in capsys.readouterr().out


def test_script_read_sends_pinned_page_and_uses_only_narrow_legacy_fallback(transport, capsys):
    calls, state = transport
    command = ['workflow', 'script', 'read', 'script1', '--workflow-id', 'w',
               '--section', 'anchors', '--revision', 'rev1', '--offset', '4', '--id', 'anchor5', '--json']
    assert main(command) == 0
    assert calls[-1].url.path.endswith('/public/script/read')
    expected = {'node_id': 'script1', 'revision': 'rev1', 'section': 'anchors',
                'offset': 4, 'ids': ['anchor5']}
    assert last_json(capsys)['body'] == expected
    state['script_http_error'] = {'code': 'script_not_found'}
    assert main(command + ['--view', 'detail']) == 1
    assert last_json(capsys)['error'] == state['script_http_error']
    assert calls[-1].url.path.endswith('/public/script/read')
    state['script_http_error'] = {'detail': 'Not Found'}
    assert main(command) == 1
    assert calls[-1].url.path.endswith('/public/script/read')
    assert main(command + ['--view', 'detail']) == 0
    assert calls[-1].url.path == '/api/v1/workflow/w/script'
    assert last_json(capsys)['body'] == {**expected, 'action': 'read', 'limit': 5}
    state.update(script_http_status=405, script_http_error={'detail': 'Method Not Allowed'})
    assert main(command + ['--view', 'detail']) == 0
    assert calls[-1].url.path == '/api/v1/workflow/w/script'


@pytest.mark.parametrize('arguments,body', [
    (['schema'], {'view': 'schema'}),
    (['schema', '--section', 'anchors'], {'view': 'schema', 'section': 'anchors'}),
    (['schema', '--field', 'shots.dialogue.speaker_id'], {'view': 'schema', 'field': 'shots.dialogue.speaker_id'}),
    (['examples', '--case', 'create-script'], {'view': 'examples', 'case': 'create-script'}),
    (['guide', '--topic', 'preflight'], {'view': 'guide', 'topic': 'preflight'}),
    (['guide', '--topic', 'anchor-prompts'], {'view': 'guide', 'topic': 'anchor-prompts'}),
    (['examples', '--case', 'reuse-scene-layout'], {'view': 'examples', 'case': 'reuse-scene-layout'}),
])
def test_script_contract_needs_no_workflow_context_or_skill(transport, capsys, arguments, body):
    calls, state = transport
    assert main(['workflow', 'script', *arguments, '--json']) == 0
    result = last_json(capsys)
    assert result['body'] == body
    assert calls[-1].url.path == '/api/v1/workflow/public/script/guide'
    assert not Path('.lightx2v').exists()
    assert all(request.method == 'GET' or request.url.path.endswith('/guide') for request in calls)


def test_script_example_payload_only_needs_case(transport, capsys):
    calls, state = transport
    assert main(['workflow', 'script', 'examples', '--payload-only']) == 2
    assert not calls
    assert last_json(capsys)['code'] == 'invalid_arguments'


def test_script_example_payload_only_and_server_upgrade_error(transport, capsys):
    calls, state = transport
    state['guide_response'] = {'payload': {'version': 1, 'items': []}, 'replace': {'version': 'current'}}
    assert main(['workflow', 'script', 'examples', '--case', 'create-script', '--payload-only']) == 0
    assert last_json(capsys) == {'version': 1, 'items': []}
    state.update(guide_response={'detail': 'Not Found'}, guide_status=404)
    assert main(['workflow', 'script', 'schema']) == 1
    assert last_json(capsys)['code'] == 'script_contract_unavailable'
    assert not Path('.lightx2v').exists()

@pytest.mark.parametrize('action,payload', [
    ('edit', {'node_id': 's', 'expected_revision': 'r', 'operations': [{'op': 'settings', 'patch': {'title': 'New'}}]}),
    ('prepare-anchors', {'node_id': 's', 'revision': 'r', 'image_settings': {'model': 'm'}, 'audio_settings': {},
                         'targets': [{'anchor_id': 'a', 'asset_kind': 'image', 'prompt': 'Blue coat'}]}),
    ('sync-anchors', {'node_id': 's'}),
    ('select-output', {'node_id': 's', 'expected_revision': 'r', 'unit_id': 'video', 'selection': None}),
])
def test_script_mutations_journal_exact_payload_without_canvas_version(transport, capsys, action, payload):
    calls, state = transport
    args = ['workflow', 'script', action, 'w', '--input', json.dumps(payload), '--operation-id', 'script-mutation', '--json']
    assert main(args) == 0
    last_json(capsys)
    request = calls[-1]
    assert request.url.path.endswith('/public/script/' + action)
    assert json.loads(request.content) == {**payload, 'operation_id': 'script-mutation'}
    assert not any(request.url.path == '/api/v1/workflow/w' for request in calls)
    journals = list(Path('.lightx2v/operations').glob('*.json'))
    assert len(journals) == 1
    record = json.loads(journals[0].read_text())
    assert record['kind'] == ('sync' if action == 'sync-anchors' else 'edit')
    assert 'apikey_fixture' not in journals[0].read_text()


def test_script_prompt_candidate_and_action_discovery_are_read_only_transport(transport, capsys):
    calls, state = transport
    body = {'node_id': 's', 'revision': 'r', 'shot_id': 'p', 'mode': 'compose'}
    assert main(['workflow', 'script', 'prompts', 'w', '--input', json.dumps(body), '--json']) == 0
    assert last_json(capsys)['body'] == body
    assert calls[-1].url.path.endswith('/script/prompts')
    assert not Path('.lightx2v').exists()
    assert main(['workflow', 'script', 'schema', '--action', 'edit', '--json']) == 0
    assert last_json(capsys)['body'] == {'view': 'schema', 'action': 'edit'}
    assert main(['workflow', 'operation', 'get', 'sync-original', '--workflow-id', 'w', '--kind', 'sync', '--json']) == 0
    assert calls[-1].url.params['kind'] == 'sync'


@pytest.mark.parametrize('known,exit_code,journal_status', [(False, 1, 'rejected'), (True, 4, 'unknown')])
def test_explicit_submission_outcome_overrides_generic_http_status(transport, capsys, known, exit_code, journal_status):
    calls, state = transport
    state['mutation_error'] = {'code': 'script_video_target_unavailable', 'outcome_unknown': known}
    assert main(['workflow', 'edit', 'w', '--input', '{"items":[]}', '--operation-id', 'explicit-outcome', '--json']) == exit_code
    last_json(capsys)
    [record] = list(Path('.lightx2v/operations').glob('*.json'))
    assert json.loads(record.read_text())['status'] == journal_status

@pytest.mark.parametrize('namespace', ['canvas', 'workflow'])
@pytest.mark.parametrize('flag', ['--canvas-id', '--workflow-id'])
def test_canvas_namespace_and_selection_aliases_share_dispatch(namespace, flag):
    args = build_parser().parse_args([namespace, 'node', 'get', 'n', flag, 'w'])
    assert args.target_workflow == 'w'
    assert args.public_operation == 'node-get'


def test_canvas_help_only_recommends_canonical_names():
    import argparse
    parser = build_parser()
    assert 'canvas' in parser.format_help()
    assert 'workflow' not in parser.format_help()
    visited = set()
    def check(current):
        if id(current) in visited:
            return
        visited.add(id(current))
        assert '--workflow-id' not in current.format_help()
        assert 'workflow script' not in current.format_help()
        assert 'workflow operation' not in current.format_help()
        for action in current._actions:
            if isinstance(action, argparse._SubParsersAction):
                for child in action.choices.values():
                    check(child)
    check(parser)


def test_canvas_alias_recovers_legacy_operation_without_new_request_identity(transport, capsys):
    calls, state = transport
    state['lost'] = True
    old = ['workflow', 'node', 'create', '--workflow-id', 'w', '--tool-id',
           'text-document', '--body', 'Keep this exact text', '--operation-id', 'shared-alias', '--json']
    assert main(old) == 4
    first = last_json(capsys)
    new = ['canvas' if item == 'workflow' else '--canvas-id' if item == '--workflow-id' else item for item in old]
    assert main(new) == 0
    result = last_json(capsys)
    assert result['operation_id'] == first['operation_id'] == 'shared-alias'
    writes = [json.loads(request.content) for request in calls if request.url.path.endswith('/edit')]
    assert len(writes) == 2 and writes[0] == writes[1]
    assert len(list(Path('.lightx2v/operations').glob('*.json'))) == 1


def test_canvas_guide_maps_topic_and_displays_only_canonical_commands(transport, capsys):
    calls, state = transport
    state['guide_response'] = {'command': 'workflow script edit --workflow-id WORKFLOW_ID --input @edit.json',
                               'steps': ['lightx2v workflow script guide --topic workflow'],
                               'payload': {'workflow_id': 'WORKFLOW_ID'}}
    assert main(['canvas', 'script', 'guide', '--topic', 'canvas', '--json']) == 0
    result = last_json(capsys)
    assert json.loads(calls[-1].content)['topic'] == 'workflow'
    assert result['command'] == 'canvas script edit --canvas-id CANVAS_ID --input @edit.json'
    assert result['steps'] == ['lightx2v canvas script guide --topic canvas']
    assert result['payload'] == {'workflow_id': 'CANVAS_ID'}


def test_command_display_does_not_rewrite_user_text():
    result = public._canonical_commands({'text': {'source': 'workflow script edit --workflow-id WORKFLOW_ID'},
                                         'workflow_id': 'owned-canvas'})
    assert result['text']['source'] == 'workflow script edit --workflow-id WORKFLOW_ID'
    assert result['workflow_id'] == 'owned-canvas'


def test_bash_completion_recommends_canvas_without_legacy_namespace():
    import subprocess
    from lightx2v.cli.commands.completion import _bash_script
    script = _bash_script() + '\nCOMP_WORDS=(lightx2v ""); COMP_CWORD=1; _lightx2v_completions; printf "%s\\n" "${COMPREPLY[@]}"\n'
    completed = subprocess.run(['bash', '-c', script], capture_output=True, text=True, check=True)
    candidates = completed.stdout.splitlines()
    assert 'canvas' in candidates and 'workflow' not in candidates
    assert {'voices', 'tts', 'voice-clone', 'doctor'} <= set(candidates)
