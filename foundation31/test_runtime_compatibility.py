"""Runtime amendment checks. Fixtures are NOT measured dense-model accuracy."""
from __future__ import annotations
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
import warnings

from .common import ROOT, CORPUS, MODEL, REVISION
from . import runtime_support as rs
from .retrieval import PinnedDenseIndex, DenseUnavailable, EvidenceService

class CompatibilityTests(unittest.TestCase):
    def test_modern_dimension_method_preferred(self):
        model=SimpleNamespace(get_embedding_dimension=lambda:384,
                              get_sentence_embedding_dimension=Mock(side_effect=AssertionError('deprecated')))
        self.assertEqual(rs.embedding_dimension(model),384)
        model.get_sentence_embedding_dimension.assert_not_called()

    def test_legacy_dimension_supported(self):
        self.assertEqual(rs.embedding_dimension(SimpleNamespace(get_sentence_embedding_dimension=lambda:384)),384)

    def test_missing_dimension_method_rejected(self):
        with self.assertRaises(AttributeError):rs.embedding_dimension(object())

    def test_noncallable_modern_uses_legacy(self):
        self.assertEqual(rs.embedding_dimension(SimpleNamespace(get_embedding_dimension=None,
                             get_sentence_embedding_dimension=lambda:384)),384)

    def test_no_tokenizer_is_explicit(self):
        self.assertEqual(rs.token_length_audit(object(),[], 'q',str)['token_length_audit_status'],'UNAVAILABLE')

    def test_diagnostic_long_text_counted_without_encoder(self):
        calls=[]
        def tokenizer(text,**kw):
            calls.append(kw)
            if kw.get('verbose',True) and len(text)>128:warnings.warn('diagnostic excess')
            return {'input_ids':list(range(len(text)))}
        model=SimpleNamespace(tokenizer=tokenizer,max_seq_length=128,encode=Mock(side_effect=AssertionError('audit cannot encode')))
        with warnings.catch_warnings(record=True) as caught:
            out=rs.token_length_audit(model,[{'chunk_id':'KR-FIXTURE','text':'x'*153}],'q'*140,lambda r:r['text'])
        self.assertEqual(len(caught),0)
        self.assertEqual(out['documents_exceeding_model_limit'],1)
        self.assertEqual(out['document_token_lengths'][0]['raw_tokens'],153)
        self.assertEqual(out['document_token_lengths'][0]['tokens_beyond_limit'],25)
        self.assertEqual(out['query_token_length']['tokens_beyond_limit'],12)
        self.assertFalse(out['diagnostic_token_ids_used_for_inference'])
        self.assertTrue(all(c==dict(add_special_tokens=True,truncation=False,verbose=False) for c in calls))
        self.assertEqual(model.max_seq_length,128)
        model.encode.assert_not_called()

    def test_exact_token_limit_not_exceeded(self):
        model=SimpleNamespace(tokenizer=lambda t,**kw:{'input_ids':[0]*128},max_seq_length=128)
        out=rs.token_length_audit(model,[{'chunk_id':'KR-X'}],'q',lambda r:'r')
        self.assertEqual(out['documents_exceeding_model_limit'],0)
        self.assertFalse(out['query_token_length']['exceeds_configured_limit'])

    def test_negative_token_limit_rejected(self):
        with self.assertRaises(ValueError):rs.token_length_audit(SimpleNamespace(tokenizer=object(),max_seq_length=-1),[],'q',str)

    def test_blocked_dependency_message(self):
        self.assertIn('Execute dense path locally',rs.next_dependency({'status':'BLOCKED_DEPENDENCY_OR_MODEL'}))

    def test_executed_dependency_message(self):
        out=rs.next_dependency({'status':'EXECUTED','performance_measured':True})
        self.assertIn('Dense path executed',out)
        self.assertNotIn('Execute dense path locally',out)
        self.assertIn('C01/C02',out)

    def test_execution_without_measurement_not_promoted(self):
        self.assertIn('Execute dense path locally',rs.next_dependency({'status':'EXECUTED','performance_measured':False}))

    def test_no_show_does_not_change_backend(self):
        with patch('matplotlib.get_backend',return_value='Agg'),patch.object(rs,'_get_shell') as shell:
            info=rs.configure_plotting(False)
        shell.assert_not_called();self.assertFalse(info['backend_reconfigured'])

    def test_existing_inline_backend_preserved(self):
        with patch('matplotlib.get_backend',return_value='module://matplotlib_inline.backend_inline'),patch.object(rs,'_get_shell') as shell:
            rs.configure_plotting(True)
        shell.assert_not_called()

    def test_existing_qtagg_backend_preserved(self):
        with patch('matplotlib.get_backend',return_value='QtAgg'),patch.object(rs,'_get_shell') as shell:
            rs.configure_plotting(True)
        shell.assert_not_called()

    def test_ipython_agg_requests_inline(self):
        shell=Mock()
        with patch('matplotlib.get_backend',side_effect=['Agg','module://matplotlib_inline.backend_inline','module://matplotlib_inline.backend_inline']),patch.object(rs,'_get_shell',return_value=shell):
            info=rs.configure_plotting(True)
        shell.run_line_magic.assert_called_once_with('matplotlib','inline')
        self.assertTrue(info['backend_reconfigured'])

    def test_headless_agg_retained(self):
        with patch('matplotlib.get_backend',return_value='Agg'),patch.object(rs,'_get_shell',return_value=None):
            info=rs.configure_plotting(True)
        self.assertEqual(info['backend_after'],'Agg')

    def test_inline_activation_error_visible(self):
        shell=Mock();shell.run_line_magic.side_effect=RuntimeError('unavailable')
        with patch('matplotlib.get_backend',return_value='Agg'),patch.object(rs,'_get_shell',return_value=shell):
            info=rs.configure_plotting(True)
        self.assertIn('unavailable',info['reconfiguration_error'])

    def test_static_backend_no_show_warning(self):
        with patch('matplotlib.get_backend',return_value='Agg'),patch.object(rs,'_get_shell',return_value=None),patch('matplotlib.pyplot.show') as show,contextlib.redirect_stdout(io.StringIO()):
            result=rs.display_figures([],True,{})
        show.assert_not_called();self.assertEqual(result['display_status'],'SAVED_NO_INTERACTIVE_BACKEND')

    def test_interactive_backend_dispatches_show(self):
        with patch('matplotlib.get_backend',return_value='module://matplotlib_inline.backend_inline'),patch('matplotlib.pyplot.show') as show:
            result=rs.display_figures([],True,{})
        show.assert_called_once();self.assertEqual(result['display_status'],'BACKEND_SHOW_DISPATCHED')

    def test_failed_activation_uses_rich_display(self):
        obj=object()
        with patch('matplotlib.get_backend',return_value='Agg'),patch.object(rs,'_get_shell',return_value=object()),patch('IPython.display.display') as display,patch('matplotlib.pyplot.close'),patch('matplotlib.pyplot.show') as show:
            result=rs.display_figures([obj],True,{})
        display.assert_called_once_with(obj);show.assert_not_called()
        self.assertEqual(result['display_status'],'IPYTHON_RICH_DISPLAY_DISPATCHED')

    def test_save_only_closes_without_show(self):
        with patch('matplotlib.get_backend',return_value='Agg'),patch('matplotlib.pyplot.show') as show:
            result=rs.display_figures([],False,{})
        show.assert_not_called();self.assertEqual(result['display_status'],'SAVE_ONLY_REQUESTED')

    def test_encode_call_ast_unchanged(self):
        before=ROOT/'docs/foundation31/runtime_compatibility_v1_0_1/before/foundation31/retrieval.py'
        after=ROOT/'foundation31/retrieval.py'
        def calls(path):
            return [ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(path.read_text()))
                    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='encode']
        self.assertEqual(calls(before),calls(after))

    def test_no_model_limit_or_chunking_change(self):
        before=ast.parse((ROOT/'docs/foundation31/runtime_compatibility_v1_0_1/before/foundation31/retrieval.py').read_text())
        after=ast.parse((ROOT/'foundation31/retrieval.py').read_text())
        def cls_func(tree,name):
            return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
        self.assertEqual(ast.dump(cls_func(before,'source_status')),ast.dump(cls_func(after,'source_status')))
        self.assertEqual(ast.dump(cls_func(before,'search')),ast.dump(cls_func(after,'search')))

    def test_fixture_encoder_rankings_before_after_match(self):
        # This is a mechanics regression, NOT real-model inference.
        import numpy as np, hashlib
        from medverse.knowledge_base.jurisdictional_semantic_kb import JurisdictionAwarePolicyKB
        before_path=ROOT/'docs/foundation31/runtime_compatibility_v1_0_1/before/foundation31/retrieval.py'
        spec=importlib.util.spec_from_file_location('foundation31._old_retrieval_fixture',before_path)
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        class FixtureEncoder:
            max_seq_length=128
            tokenizer=staticmethod(lambda t,**kw:{'input_ids':list(range(len(t.split())+2))})
            def encode(self,texts,normalize_embeddings=True,convert_to_numpy=True):
                values=[]
                for t in texts:
                    raw=hashlib.shake_256(t.encode()).digest(384)
                    v=np.frombuffer(raw,dtype=np.uint8).astype(float)+1
                    values.append(v/np.linalg.norm(v))
                return np.asarray(values)
        previous=old.EvidenceService('dense');current=EvidenceService('dense')
        previous.dense.model=FixtureEncoder();current.dense.model=FixtureEncoder()
        families=json.loads((ROOT/'data/final_validation/query_families.json').read_text())['records']
        for f in families:
            for lang in ('en','ko'):
                a=previous.search(f[lang],f['role']);b=current.search(f[lang],f['role'])
                self.assertEqual([(h['chunk_id'],h['score']) for h in a['hits']],[(h['chunk_id'],h['score']) for h in b['hits']])
                self.assertEqual(a['rejected'],b['rejected'])

    def test_pinned_loader_modern_api(self):
        class Fixture:
            max_seq_length=128
            def eval(self):return self
            def get_embedding_dimension(self):return 384
            def get_sentence_embedding_dimension(self):raise AssertionError('deprecated API called')
            def __getitem__(self,key):return SimpleNamespace(auto_model=SimpleNamespace(config=SimpleNamespace(_commit_hash=None)))
        construct=Mock(return_value=Fixture())
        with patch.dict(sys.modules,{'sentence_transformers':SimpleNamespace(SentenceTransformer=construct)}),patch('foundation31.retrieval.md.version',return_value='fixture-test-only'):
            model=PinnedDenseIndex([]);model.load_model()
        self.assertEqual(construct.call_args.kwargs['revision'],REVISION)
        self.assertEqual(model.metadata['actual_dimension'],384)
        self.assertEqual(model.metadata['max_seq_length'],128)

    def test_wrong_dimension_still_rejected(self):
        fixture=SimpleNamespace(eval=lambda:None,get_embedding_dimension=lambda:768)
        with patch.dict(sys.modules,{'sentence_transformers':SimpleNamespace(SentenceTransformer=lambda *a,**kw:fixture)}):
            with self.assertRaisesRegex(DenseUnavailable,'WRONG_EMBEDDING_DIMENSION'):PinnedDenseIndex([]).load_model()

    def test_missing_model_explicit_no_fallback(self):
        k=EvidenceService('dense')
        k.dense.load_model=lambda:(_ for _ in ()).throw(DenseUnavailable('TEST_UNAVAILABLE'))
        out=k.search('research data','privacy_agent')
        self.assertEqual(out['status'],'BLOCKED_DENSE_BACKEND')
        self.assertFalse(out['fallback_used'])

if __name__=='__main__':unittest.main(verbosity=2)
