from entry_hold_v125 import EntryHold as FrozenEntryHold

class EntryHold(FrozenEntryHold):
    """Single-episode diagnostic: resume the original path after a batch hold barrier."""
    def __init__(self,*args,**kwargs):
        self.released=False;self.release_times=None
        super().__init__(*args,**kwargs)
    def apply(self,actions):
        if self.released:
            return self.original_apply(actions)
        return super().apply(actions)
    def release_original_path(self):
        assert not self.released
        self.c.safe_approach_waypoints[14]=self.original_next
        self.release_times=(self.env.episode_length_buf*self.env.step_dt).clone()
        self.released=True
    def summary(self):
        result=super().summary()
        result.update(resume_scope='All active environments must finish actual final-body settling before globally restoring original waypoint14. No readiness/contact flags forced; legs remain under final-body hold.',
            original_path_released=self.released,release_time_s=self.release_times.cpu().tolist() if self.release_times is not None else None)
        return result
