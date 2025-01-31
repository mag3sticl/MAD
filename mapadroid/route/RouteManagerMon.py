import time

from mapadroid.route.RouteManagerBase import RouteManagerBase
from mapadroid.utils.logging import LoggerEnums, get_logger

logger = get_logger(LoggerEnums.routemanager)


class RouteManagerMon(RouteManagerBase):
    def __init__(self, db_wrapper, dbm, area_id, coords, max_radius, max_coords_within_radius,
                 path_to_include_geofence,
                 path_to_exclude_geofence, routefile, mode=None, coords_spawns_known=True, init=False,
                 name="unknown", settings=None, joinqueue=None, include_event_id=None):

        RouteManagerBase.__init__(self, db_wrapper=db_wrapper, dbm=dbm, area_id=area_id, coords=coords,
                                  max_radius=max_radius,
                                  max_coords_within_radius=max_coords_within_radius,
                                  path_to_include_geofence=path_to_include_geofence,
                                  path_to_exclude_geofence=path_to_exclude_geofence,
                                  routefile=routefile, init=init,
                                  name=name, settings=settings, mode=mode, joinqueue=joinqueue
                                  )
        self.coords_spawns_known = coords_spawns_known
        self.include_event_id = include_event_id

    def _priority_queue_update_interval(self):
        return 600

    def _get_coords_after_finish_route(self) -> bool:
        self._init_route_queue()
        return True

    def _recalc_route_workertype(self):
        self.recalc_route(self._max_radius, self._max_coords_within_radius, 1, delete_old_route=True,
                          in_memory=False)
        self._init_route_queue()

    def _retrieve_latest_priority_queue(self):
        return self.db_wrapper.retrieve_next_spawns(self.geofence_helper)

    def _get_coords_post_init(self):
        if self.coords_spawns_known:
            self.logger.info("Reading known Spawnpoints from DB")
            coords = self.db_wrapper.get_detected_spawns(
                self.geofence_helper, self.include_event_id)
        else:
            self.logger.info("Reading unknown Spawnpoints from DB")
            coords = self.db_wrapper.get_undetected_spawns(
                self.geofence_helper, self.include_event_id)
        self._start_priority_queue()
        return coords

    def _cluster_priority_queue_criteria(self):
        if self.settings is not None:
            return self.settings.get("priority_queue_clustering_timedelta", 300)
        else:
            return 300

    def _should_skip_prioq_entry(self, queue_entry) -> bool:
        # Override the base class:
        # TODO: Consider if we want to have the following functionality for other modes, too
        # Problem: delete_seconds_passed = 0 makes sense in _filter_priority_queue_internal,
        # because it will remove past events only at the moment of prioQ calculation,
        # but here it would skip ALL events, because events can only be due when they are in the past
        if self.remove_from_queue_backlog in [None, 0]:
            return False
        delete_before = time.time() - self.remove_from_queue_backlog
        return queue_entry[0] < delete_before

    def _start_routemanager(self):
        with self._manager_mutex:
            if not self._is_started:
                self._is_started = True
                self.logger.info("Starting routemanager {}", self.name)
                if not self.init:
                    self._start_priority_queue()
                self._start_check_routepools()
                self._init_route_queue()
        return True

    def _delete_coord_after_fetch(self) -> bool:
        return False

    def _quit_route(self):
        self.logger.info('Shutdown Route {}', self.name)
        self._is_started = False
        self._round_started_time = None

    def _check_coords_before_returning(self, lat, lng, origin):
        return True
