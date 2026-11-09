"""Compatibility, diagnostics and display only; no scientific parameter changes."""
from __future__ import annotations
from typing import Any

_STATIC_BACKENDS = {"agg", "pdf", "ps", "svg", "pgf", "cairo", "template",
                    "module://matplotlib.backends.backend_agg"}

def embedding_dimension(model: Any) -> int | None:
    """Prefer the current name; remain compatible with the archived library API."""
    method = getattr(model, "get_embedding_dimension", None)
    if callable(method):
        return method()
    method = getattr(model, "get_sentence_embedding_dimension", None)
    if callable(method):
        return method()
    raise AttributeError("Model has no supported embedding-dimension method")

def token_length_audit(model: Any, records: list, query: str, text_fn) -> dict:
    """Count original tokens; do not feed the untruncated IDs to the encoder.

    verbose=False applies ONLY to these intentionally untruncated diagnostics.
    Actual model.encode calls, tokenizer limits and warnings remain untouched.
    Counts identify potential truncation, not proof of a retrieval-error cause.
    """
    tokenizer = getattr(model, "tokenizer", None)
    limit = getattr(model, "max_seq_length", None)
    if tokenizer is None or limit is None:
        return {"token_length_audit_status": "UNAVAILABLE"}
    limit = int(limit)
    if limit < 1:
        raise ValueError("Invalid configured model sequence limit")
    def count(text):
        return len(tokenizer(text, add_special_tokens=True,
                             truncation=False, verbose=False)["input_ids"])
    documents=[]
    for record in records:
        n=count(text_fn(record))
        documents.append({"policy_id":record["chunk_id"], "raw_tokens":n,
                          "exceeds_configured_limit":n>limit,
                          "tokens_beyond_limit":max(0,n-limit)})
    query_count=count(query)
    return {
        "token_length_audit_status":"COUNTED_WITHOUT_MODEL_INFERENCE",
        "model_token_limit":limit,
        "documents_exceeding_model_limit":sum(d["exceeds_configured_limit"] for d in documents),
        "document_token_lengths":documents,
        "query_token_length":{"raw_tokens":query_count,
                              "exceeds_configured_limit":query_count>limit,
                              "tokens_beyond_limit":max(0,query_count-limit)},
        "truncation_policy":"original model limit; no post-result chunking changes",
        "diagnostic_token_ids_used_for_inference":False,
        "encoding_parameters_changed":False,
    }

def _get_shell():
    try:
        from IPython import get_ipython
        return get_ipython()
    except ImportError:
        return None

def configure_plotting(show: bool) -> dict:
    """Respect interactive backends; recover Agg to inline only inside IPython."""
    import matplotlib
    before=str(matplotlib.get_backend())
    info={"requested_show":bool(show), "backend_before":before,
          "backend_after":before, "backend_reconfigured":False,
          "reconfiguration_error":None}
    if show and before.lower() in _STATIC_BACKENDS:
        shell=_get_shell()
        if shell is not None:
            try:
                # In Spyder/IPython this enables its Plots/inline integration.
                shell.run_line_magic("matplotlib", "inline")
                info["backend_reconfigured"]=str(matplotlib.get_backend())!=before
            except Exception as exc:
                info["reconfiguration_error"]=f"{type(exc).__name__}: {exc}"
    info["backend_after"]=str(matplotlib.get_backend())
    return info

def display_figures(figures: list, show: bool, info: dict) -> dict:
    import matplotlib
    import matplotlib.pyplot as plt
    result=dict(info)
    result["backend_after"]=str(matplotlib.get_backend())
    if not show:
        for fig in figures: plt.close(fig)
        result["display_status"]="SAVE_ONLY_REQUESTED"
    elif str(matplotlib.get_backend()).lower() in _STATIC_BACKENDS:
        if _get_shell() is not None:
            # A failed GUI/inline activation must not cause an Agg .show warning.
            from IPython.display import display
            for fig in figures:
                display(fig)
                plt.close(fig)
            result["display_status"]="IPYTHON_RICH_DISPLAY_DISPATCHED"
        else:
            for fig in figures: plt.close(fig)
            result["display_status"]="SAVED_NO_INTERACTIVE_BACKEND"
            print("Figures saved. No interactive backend is active in this process. "
                  "For Spyder use %matplotlib inline, then the same gate's --plot-only option.")
    else:
        plt.show()
        result["display_status"]="BACKEND_SHOW_DISPATCHED"
    return result

def next_dependency(dense: dict) -> str:
    if dense.get("status")=="EXECUTED" and dense.get("performance_measured") is True:
        return ("Dense path executed. Retain measured bilingual differences; audit token "
                "coverage and model-revision provenance. Next scientific task: frozen-design "
                "Gate32 commitment control; C01/C02 remain unresolved in this gate.")
    return ("Execute dense path locally where dependencies and pinned weights are available, "
            "then implement frozen-design Gate32 commitment control; this gate does not "
            "repair eager commits.")
