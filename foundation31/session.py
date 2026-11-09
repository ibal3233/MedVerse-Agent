"""Live observational bridge; frozen Gate 30 action semantics are unchanged."""
from coordination30.engine import IntegratedSession
from .digital_twin import ReleasedSnapshotBridge
class FoundationSession(IntegratedSession):
    def __init__(self,*args,**kwargs):
        self.dt_bridge=ReleasedSnapshotBridge()
        super().__init__(*args,**kwargs)
        self.dt_bridge.update(super().snapshot())
    def advance(self,auto_commit=True):
        super().advance(auto_commit)
        self.dt_bridge.update(super().snapshot())
        return self.snapshot()
    def snapshot(self):
        s=super().snapshot()
        s['foundation31']=self.dt_bridge.snapshot()
        s['foundation31']['implementation_status']='DT_AND_EVIDENCE_BRIDGE_ONLY; COMMIT_TIMING_NOT_CHANGED'
        return s
