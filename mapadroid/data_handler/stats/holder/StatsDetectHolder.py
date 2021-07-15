import time
from datetime import datetime

from mapadroid.data_handler.stats.holder.AbstractStatsHolder import AbstractStatsHolder
from mapadroid.data_handler.AbstractWorkerHolder import AbstractWorkerHolder
from sqlalchemy.ext.asyncio import AsyncSession

from mapadroid.db.model import TrsStatsDetect


class StatsDetectEntry(TrsStatsDetect):
    def __init__(self, worker: str):
        super().__init__()
        self.worker = worker
        self.timestamp_scan = time.time()
        self.mon = 0
        self.raid = 0
        self.mon_iv = 0
        self.quest = 0

    def update(self, time_scanned: datetime, new_mons: int = 0, new_raids: int = 0, new_mon_ivs: int = 0,
               new_quests: int = 0):
        self.mon += new_mons
        self.raid += new_raids
        self.mon_iv += new_mon_ivs
        self.quest += new_quests
        if time_scanned.timestamp() > self.timestamp_scan:
            self.timestamp_scan = time_scanned.timestamp()


class StatsDetectHolder(AbstractStatsHolder, AbstractWorkerHolder):
    def __init__(self, worker: str):
        # Wild mon encounterID to counts seen mapping
        AbstractWorkerHolder.__init__(self, worker)
        self._entry: StatsDetectEntry = StatsDetectEntry(worker)

    async def submit(self, session: AsyncSession) -> None:
        async with session.begin_nested() as nested:
            self._entry.timestamp_scan = time.time()
            session.add(self._entry)
            await nested.commit()
            # TODO: Catch IntegrityError/handle update

    def add_mon(self, time_scanned: datetime) -> None:
        self._entry.update(time_scanned, new_mons=1)

    def add_raid(self, time_scanned: datetime) -> None:
        self._entry.update(time_scanned, new_raids=1)

    def add_mon_iv(self, time_scanned: datetime) -> None:
        self._entry.update(time_scanned, new_mon_ivs=1)

    def add_quest(self, time_scanned: datetime) -> None:
        self._entry.update(time_scanned, new_quests=1)
