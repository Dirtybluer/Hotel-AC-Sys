import datetime

import logging

from Service.models import Service as ServiceModel


def singleton(ctrl):
    _instance = {}

    def inner():
        if ctrl not in _instance:
            _instance[ctrl] = ctrl()
        return _instance[ctrl]

    return inner


@singleton
class Controller:
    # 2 种调度模式
    TIME_SLICE_MODE = 0
    PRIOR_MODE = 1

    # 3 种服务状态
    WAITING = 1
    ACTIVE = 2
    SLEEPING = 3

    # 控制系统的参数设置
    settings = {
        'mode': 0,
        'tempHighLimit': 0,
        'tempLowLimit': 0,
        'defaultTargetTemp': 25,
        'defaultFanSpeed': 2,
        'FeeRateH': 0,
        'FeeRateM': 0,
        'FeeRateL': 0,
        'dispatchMode': PRIOR_MODE,
        'serviceLimit': 3,
        'timeSlice': 2
    }

    # 房间信息记录
    room_state = [
        {'roomId': 0,
         'AC_status': 0,
         'currentTemp': 0,
         'targetTemp': 0,
         'fan': 0,
         'feeRate': 0,
         'fee': 0,
         'duration': 0,
         'timesOfOnOff': 0,
         'timesOfDispatch': 0,
         'timesOfChangeTemp': 0,
         'timesOfChangeFanSpeed': 0},
        {'roomId': 1,
         'AC_status': 0,
         'currentTemp': 0,
         'targetTemp': 0,
         'fan': 0,
         'feeRate': 0,
         'fee': 0,
         'duration': 0,
         'timesOfOnOff': 0,
         'timesOfDispatch': 0,
         'timesOfChangeTemp': 0,
         'timesOfChangeFanSpeed': 0},
        {'roomId': 2,
         'AC_status': 0,
         'currentTemp': 0,
         'targetTemp': 0,
         'fan': 0,
         'feeRate': 0,
         'fee': 0,
         'duration': 0,
         'timesOfOnOff': 0,
         'timesOfDispatch': 0,
         'timesOfChangeTemp': 0,
         'timesOfChangeFanSpeed': 0},
        {'roomId': 3,
         'AC_status': 0,
         'currentTemp': 0,
         'targetTemp': 0,
         'fan': 0,
         'feeRate': 0,
         'fee': 0,
         'duration': 0,
         'timesOfOnOff': 0,
         'timesOfDispatch': 0,
         'timesOfChangeTemp': 0,
         'timesOfChangeFanSpeed': 0},
        {'roomId': 4,
         'AC_status': 0,
         'currentTemp': 0,
         'targetTemp': 0,
         'fan': 0,
         'feeRate': 0,
         'fee': 0,
         'duration': 0,
         'timesOfOnOff': 0,
         'timesOfDispatch': 0,
         'timesOfChangeTemp': 0,
         'timesOfChangeFanSpeed': 0},
    ]

    # 3 种服务状态对应的队列
    active_services = []
    waiting_services = []
    sleeping_services = []

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)

    def print_log(self):
        """
        打印服务队列，等待队列，睡眠队列的内容
        """

        print('active_services:')
        for service_item in self.active_services:
            print(service_item.__str__())
        print('waiting_services:')
        for service_item in self.waiting_services:
            print(service_item.__str__())
        print('sleeping_services:')
        for service_item in self.sleeping_services:
            print(service_item.__str__())

    def _get_fee_rate(self, fan_speed):
        if fan_speed == 1:
            return self.settings['FeeRateL']
        elif fan_speed == 2:
            return self.settings['FeeRateM']
        elif fan_speed == 3:
            return self.settings['FeeRateH']
        else:
            raise RuntimeError('fan speed is not allowed')

    def _get_dispatch_mode(self):
        """
        获取系统调度模式
        """
        return self.settings['dispatchMode']

    def _get_active_service(self, room_id):
        """
         通过房间 ID 在服务队列中寻找服务
        """
        for active_service in self.active_services:
            if active_service.room_id == room_id:
                return active_service
        return None

    def _get_waiting_service(self, room_id):
        """
            通过房间 ID 在等待队列中寻找服务
        """
        for waiting_service in self.waiting_services:
            if waiting_service.room_id == room_id:
                return waiting_service
        return None

    def _get_sleeping_service(self, room_id):
        """
            通过房间 ID 在睡眠队列中寻找服务
        """
        for sleeping_service in self.sleeping_services:
            if sleeping_service.room_id == room_id:
                return sleeping_service
        return None

    def _get_service(self, room_id):
        """
            通过房间 ID 在睡眠队列中寻找服务
        """
        if self._get_active_service(room_id) is not None:
            return self._get_active_service(room_id)
        elif self._get_waiting_service(room_id) is not None:
            return self._get_waiting_service(room_id)
        elif self._get_sleeping_service(room_id) is not None:
            return self._get_waiting_service(room_id)
        else:
            raise RuntimeError('Service not found')

    def _get_pr_replaced_service(self, alter_service):
        """
        根据优先级模式下的策略返回被替代的服务
        """

        replaced_service = None

        for active_service in self.active_services:
            if active_service.fan_speed < alter_service.fan_speed:
                if replaced_service is None \
                        or active_service.fan_speed < replaced_service.fan_speed \
                        or (active_service.fan_speed == replaced_service.fan_speed
                            and active_service.get_duration() > replaced_service.get_duration()):
                    replaced_service = active_service

        return replaced_service

    def _is_all_speed_equal(self):
        """
        比较等待队列和服务队列中的所有服务的风速，判断是否都相等
        """

        if len(self.active_services) == 0:
            return True
        else:
            std_service = self.active_services[0]
            for service in self.active_services:
                if service.fan_speed != std_service.fan_speed:
                    return False
            for service in self.waiting_services:
                if service.fan_speed != std_service.fan_speed:
                    return False
            return True

    def _get_max_speed_waiting_service(self):
        if len(self.waiting_services) == 0:
            return None
        service = self.waiting_services[0]
        for waiting_service in self.waiting_services:
            if waiting_service.fan_speed > service.fan_speed:
                service = waiting_service
        return service

    @staticmethod
    def _get_max_duration_waiting_service(temp_waiting_services):
        max_waiting_service = temp_waiting_services[0]
        for waiting_service in temp_waiting_services:
            if waiting_service.get_ts_duration() > max_waiting_service.get_ts_duration():
                max_waiting_service = waiting_service
        return max_waiting_service

    def _get_ts_finished_service(self):
        """
        在时间片调度模式下，找出当前服务队列中已完成时间片，且服务时间最长的服务

        """

        alter_services = []
        for service in self.active_services:
            if service.get_ts_duration() >= self.settings['timeSlice'] * 60:
                alter_services.append(service)

        if len(alter_services) == 0:
            return None
        else:
            alter_service = alter_services[0]
            for service in alter_services:
                if service.get_ts_duration() > alter_service.get_ts_duration():
                    alter_service = service
            return alter_service

    def _change_dispatch_mode(self, target_mode):
        """
        改变调度模式。
        """

        self.settings['dispatchMode'] = target_mode

        if target_mode == self.TIME_SLICE_MODE:
            for service in self.active_services:
                service.time_slice_begin_time = datetime.datetime.now()
            for service in self.waiting_services:
                service.time_slice_begin_time = datetime.datetime.now()
        else:
            for service in self.active_services:
                service.time_slice_begin_time = -1
            for service in self.waiting_services:
                service.time_slice_begin_time = -1

    def _replace(self, active_service, waiting_service):
        """
        替换原本服务队列中的服务。
        1. 持久化被替换服务
        2. 将被替换服务从服务队列中移出服务队列，重置 time 和 fee，移入等待队列
        3. 将候选服务加入服务队列中，并初始化 time
        """

        dispatch_mode = self._get_dispatch_mode()
        if dispatch_mode == self.TIME_SLICE_MODE:
            active_service.time_slice_begin_time = datetime.datetime.now()
            waiting_service.time_slice_begin_time = datetime.datetime.now()

        active_service.service_finish_time = datetime.datetime.now()
        active_service.save2db()
        self.room_state[active_service.room_id]['duration'] += active_service.get_duration()
        self.room_state[active_service.room_id]['fee'] += active_service.get_fee()
        self.active_services.remove(active_service)
        active_service.service_begin_time = -1
        active_service.waiting_service = datetime.datetime.now()
        self.waiting_services.append(active_service)
        self.room_state[active_service.room_id]['timesOfDispatch'] += 1
        self.room_state[active_service.room_id]['AC_status'] = 1

        self.waiting_services.remove(waiting_service)
        waiting_service.service_begin_time = datetime.datetime.now()
        waiting_service.waiting_begin_time = -1
        self.active_services.append(waiting_service)
        self.room_state[waiting_service.room_id]['timesOfDispatch'] += 1
        self.room_state[waiting_service.room_id]['AC_status'] = 2

    def _update_dispatch_by_pr(self):
        """
        使用优先级模式更新调度。
        1. 选取等待队列中风速最大的服务作为候选服务，该服务是唯一有可能被调度的服务, 如果等待队列中无服务就不调度。
        2. 判断服务队列的状态
            - 如果未满则直接将候选服务放入
            - 如果已满
                - 如果两个队列中的服务的风速都与候选服务相等，则初始化所有服务的 time_slice_begin_time，切换到时间片调度
                - 如果服务队列中有比候选服务风速更小的服务，找出其中风速最小的服务，如果有多个风速最小的服务，找出其中服务时长最长的将其置换
                - 否则候选服务继续等待

        """

        if len(self.waiting_services) == 0:
            return

        controller = Controller()
        alter_service = self._get_max_speed_waiting_service()
        if len(self.active_services) < controller.settings['serviceLimit']:
            self.waiting_services.remove(alter_service)
            alter_service.waiting_begin_time = -1
            alter_service.service_begin_time = datetime.datetime.now()
            self.active_services.append(alter_service)
            self.room_state[alter_service.room_id]['timesOfDispatch'] += 1
            self.room_state[alter_service.room_id]['AC_status'] = 2
        else:
            replaced_service = self._get_pr_replaced_service(alter_service)
            if self._is_all_speed_equal():
                self._change_dispatch_mode(controller.TIME_SLICE_MODE)
                self._update_dispatch_by_ts()
            elif replaced_service is not None:
                self._replace(replaced_service, alter_service)

    def _update_dispatch_by_ts(self):
        """
        使用时间片模式调度
        *** 在时间片模式下，计算服务在队列中的服务或者等待时间时，使用的是 time_slice_begin_time，但是计算费用时依然需要
            使用 get_duration。每次调度时依然需要设置 service_begin_time 和 waiting_begin_time，以备将来切换
            到优先级模式沿用。

        判断两个队列中的风速是否全部相等
        - 如果不相等，切换到优先级调度
        - 如果相等
        1. 暂存当前等待队列（防止重复判断刚被置换出的服务），每次选取等待队列中的等待时间最长的服务作为候选服务。如果等待队列中无服务则不调度。
        2. 判断服务队列的状态
            - 如果未满则直接将候选服务放入，重置服务的 time_slice_begin_time。
            - 如果已满
                - 如果服务队列中有完成时间片的服务，则将其置换出来。持久化被替换的服务，重置被替换服务的 fee，
                重置两个服务的 time_slice_begin_time
                - 否则候选服务继续等待

        """

        controller = Controller()
        if not self._is_all_speed_equal():
            self._change_dispatch_mode(controller.PRIOR_MODE)
            self._update_dispatch_by_pr()
        else:
            if len(self.waiting_services) == 0:
                return

            controller = Controller()
            temp_waiting_services = self.waiting_services.copy()
            while len(temp_waiting_services) != 0:
                alter_service = self._get_max_duration_waiting_service(temp_waiting_services)
                temp_waiting_services.remove(alter_service)
                # 找到真正的 alter_service
                alter_service = self._get_waiting_service(alter_service.room_id)
                if len(self.active_services) < controller.settings['serviceLimit']:
                    self.waiting_services.remove(alter_service)
                    alter_service.time_slice_begin_time = datetime.datetime.now()
                    alter_service.service_begin_time = datetime.datetime.now()
                    alter_service.waiting_begin_time = -1
                    self.active_services.append(alter_service)
                    self.room_state[alter_service.room_id]['timesOfDispatch'] += 1
                else:
                    replaced_service = self._get_ts_finished_service()
                    if replaced_service is not None:
                        self._replace(replaced_service, alter_service)
                    else:
                        return

    def _dispatch(self):
        """
        调度函数。根据当前调度模式有优先级调度和时间片调度 2 种方式。
        可能发生调度的请况：
            1. 空调开机
            2. 空调关机
            3. 变速请求
            4. 达到设定温度
            5. 回温后再次请求
        """

        dispatch_mode = self._get_dispatch_mode()
        if dispatch_mode == self.PRIOR_MODE:
            update_dispatch = self._update_dispatch_by_pr
        else:
            update_dispatch = self._update_dispatch_by_ts

        update_dispatch()

    def request_on(self, service):
        self.room_state[service.room_id]['targetTemp'] = service.target_temp
        self.room_state[service.room_id]['fan'] = service.fan_speed
        self.room_state[service.room_id]['feeRate'] = service.fee_rate

        self.room_state[service.room_id]['timesOfOnOff'] += 1

        dispatch_mode = self._get_dispatch_mode()
        service.waiting_begin_time = datetime.datetime.now()
        if dispatch_mode == self.TIME_SLICE_MODE:
            service.time_slice_begin_time = datetime.datetime.now()
        self.waiting_services.append(service)
        self.room_state[service.room_id]['AC_status'] = 1

        self._dispatch()

        if service in self.active_services:
            return self.ACTIVE
        elif service in self.waiting_services:
            self.room_state[service.room_id]['timesOfDispatch'] += 1
            return self.WAITING
        else:
            raise RuntimeError('Service not found')

    def change_target_temp(self, room_id, target_temp):
        """
        改变房间的目标温度。
        在队列中找到该服务，直接改变服务信息中的目标温度
        """
        service = self._get_service(room_id)
        service.target_temp = target_temp

        self.room_state[service.room_id]['timesOfChangeTemp'] += 1
        self.room_state[room_id]['targetTemp'] = target_temp

    def change_fan_speed(self, room_id, fan_speed):
        """
        改变房间的风速。
        - 如果该服务位于等待队列，改变服务信息中的目标风速，尝试调度
        - 如果该服务为位于服务队列：
            1. 持久化该服务
            2. 改变服务信息中的风速
            3. 重置新服务开始时间
            4. 尝试调度
        """
        service = self._get_service(room_id)
        service.fan_speed = fan_speed
        service.fee_rate = self._get_fee_rate(fan_speed)
        self.room_state[service.room_id]['timesOfChangeFanSpeed'] += 1
        self.room_state[room_id]['fan'] = service.fan_speed
        self.room_state[room_id]['feeRate'] = service.fee_rate

        if service in self.active_services:
            self.room_state[room_id]['fee'] += service.get_fee()
            self.room_state[room_id]['duration'] += service.get_duration()
            service.service_finish_time = datetime.datetime.now()
            service.save2db()
            service.service_begin_time = datetime.datetime.now()

        if service not in self.sleeping_services:
            self._dispatch()

    def request_off(self, room_id):
        service = self._get_service(room_id)

        if service in self.waiting_services:
            self.waiting_services.remove(service)
        elif service in self.active_services:
            self.active_services.remove(service)
            service.service_finish_time = datetime.datetime.now()
            service.save2db()
            self._dispatch()
        elif service in self.sleeping_services:
            self.sleeping_services.remove(service)

        self.room_state[room_id]['AC_status'] = 0

    def pause_service(self, room_id):
        """
        在房间温度到达设定温度时，暂停服务。
        持久化本次服务,将服务从服务队列中取出，放入睡眠队列，尝试调度（由于模拟的限制，服务可能在等待队列中）
        """

        service = self._get_service(room_id)
        self.sleeping_services.append(service)
        self.room_state[service.room_id]['timesOfDispatch'] += 1
        self.room_state[room_id]['AC_status'] = 4

        if service in self.active_services:
            self.room_state[room_id]['fee'] += service.get_fee()
            self.room_state[room_id]['duration'] += service.get_duration()
            service.service_finish_time = datetime.datetime.now()
            service.save2db()
            self.active_services.remove(service)
            self._dispatch()
        elif service in self.waiting_services:
            self.waiting_services.remove(service)

    def resume_service(self, room_id):
        """
        在房间温度恢复到阈值时，继续服务。
        将服务从睡眠队列中取出，重置 time，fee，放入等待队列，尝试调度
        """
        service = self._get_service(room_id)
        self.sleeping_services.remove(service)
        service.service_begin_time = -1
        service.waiting_begin_time = datetime.datetime.now()
        dispatch_mode = self._get_dispatch_mode()
        if dispatch_mode == self.TIME_SLICE_MODE:
            service.time_slice_begin_time = datetime.datetime.now()

        self.waiting_services.append(service)
        self.room_state[service.room_id]['timesOfDispatch'] += 1
        self.room_state[room_id]['AC_status'] = 1
        self._dispatch()

    def update_room_temp(self, room_id, room_temp):
        self.room_state[room_id]['currentTemp'] = room_temp

    def get_room_fee(self, room_id):
        """
        获取当前房间使用空调的总费用。
        如果当前房间在服务对列中，则费用等于已持久化的详单费用和加上服务队列中的费用，
        否则就等于已持久化的详单费用和。
        """
        fee = self.room_state[room_id]['fee']

        active_service = self._get_active_service(room_id)
        if active_service is not None:
            fee += active_service.get_fee()

        return fee

    def get_room_duration(self, room_id):
        duration = self.room_state[room_id]['duration']

        active_service = self._get_active_service(room_id)
        if active_service is not None:
            duration += active_service.get_duration()

        return duration

    def get_room_state(self):
        room_state = []
        # 单独更新实时的 fee 和 duration，duration 转换为分钟
        for state in self.room_state:
            room_state.append({
                'roomId': state['roomId'],
                'AC_status': state['AC_status'],
                'currentTemp': state['currentTemp'],
                'targetTemp': state['targetTemp'],
                'fan': state['fan'],
                'feeRate': state['feeRate'],
                'fee': self.get_room_fee(state['roomId']),
                'duration': round(self.get_room_duration(state['roomId']) / 60, 2)
            })

        return room_state

    @staticmethod
    def get_DRD(date_in, date_out):
        services = ServiceModel.objects.filter(request_time__gte=date_in) \
            .filter(finish_time__lte=date_out).order_by('request_time')
        DRD = []
        for service in services:
            DRD.append({
                'num': service.id,
                'roomId': service.room_id,
                'requestTime': (service.request_time+datetime.timedelta(hours=8)).strftime('%H:%M'),
                'requestDuration': service.request_duration,
                'fanSpeed': service.fan_speed,
                'feeRate': service.fee_rate,
                'fee': service.fee
            })
        return DRD

    @staticmethod
    def get_bill(date_in, date_out):
        total_fee = 0
        services = ServiceModel.objects.filter(request_time__gte=date_in) \
            .filter(finish_time__lte=date_out).order_by('request_time')
        for service in services:
            total_fee += service.fee
        return total_fee

    def get_report(self, date, report_type):
        report = []
        if report_type == 0:
            for i in len(self.room_state):
                report.append({
                    'roomId': i,
                    'timesOfOnOff': self.room_state[i]['timesOfOnOff'],
                    'duration': self.room_state[i]['duration'],
                    'totalFee': self.room_state[i]['fee'],
                    'timesOfDispatch': self.room_state[i]['timesOfDispatch'],
                    'numberOfRDR': len(ServiceModel.objects.filter(room_id=i).filter(request_time__day=date.date.day)),
                    'timesOfChangeTemp': self.room_state[i]['timesOfChangeTemp'],
                    'timesOfChangeFanSpeed': self.room_state[i]['timesOfChangeFanSpeed']
                })
        elif report_type == 1:
            for i in range(len(self.room_state)):
                report.append({
                    'roomId': i,
                    'timesOfOnOff': self.room_state[i]['timesOfOnOff'],
                    'duration': self.room_state[i]['duration'],
                    'totalFee': self.room_state[i]['fee'],
                    'timesOfDispatch': self.room_state[i]['timesOfDispatch'],
                    'numberOfRDR': len(
                        ServiceModel.objects.filter(room_id=i).filter(request_time__day=date.month)),
                    'timesOfChangeTemp': self.room_state[i]['timesOfChangeTemp'],
                    'timesOfChangeFanSpeed': self.room_state[i]['timesOfChangeFanSpeed']
                })
        elif report_type == 2:
            for i in len(self.room_state):
                report.append({
                    'roomId': i,
                    'timesOfOnOff': self.room_state[i]['timesOfOnOff'],
                    'duration': self.room_state[i]['duration'],
                    'totalFee': self.room_state[i]['fee'],
                    'timesOfDispatch': self.room_state[i]['timesOfDispatch'],
                    'numberOfRDR': len(ServiceModel.objects.filter(room_id=i).filter(request_time=date.date.month)),
                    'timesOfChangeTemp': self.room_state[i]['timesOfChangeTemp'],
                    'timesOfChangeFanSpeed': self.room_state[i]['timesOfChangeFanSpeed']
                })
        elif report_type == 3:
            for i in len(self.room_state):
                report.append({
                    'roomId': i,
                    'timesOfOnOff': self.room_state[i]['timesOfOnOff'],
                    'duration': self.room_state[i]['duration'],
                    'totalFee': self.room_state[i]['fee'],
                    'timesOfDispatch': self.room_state[i]['timesOfDispatch'],
                    'numberOfRDR': len(
                        ServiceModel.objects.filter(room_id=i).filter(request_time__year=date.date.year)),
                    'timesOfChangeTemp': self.room_state[i]['timesOfChangeTemp'],
                    'timesOfChangeFanSpeed': self.room_state[i]['timesOfChangeFanSpeed']
                })

        return report


class Service:
    """
    room_id: 房间的ID
    waiting_begin_time: 进入等待队列的时间
    service_begin_time: 进入服务队列的时间
    time_slice_begin_time: 开始进入时间片轮转调度的时间
        - 对于等待队列里的服务是时间片模式下等待开始时间
        - 对于服务队列里的服务是时间片模式下服务开始时间
    fan_speed: 风速
    """

    def __init__(self, room_id, mode, target_temp, fan_speed=2):
        controller = Controller()
        self.room_id = room_id
        self.mode = mode
        self.fan_speed = fan_speed
        self.target_temp = target_temp
        self.fee_rate = controller.settings['FeeRateM']
        self.service_begin_time = -1
        self.service_finish_time = -1
        self.time_slice_begin_time = -1
        self.time_of_dispatch = 0
        self.time_of_change_temp = 0
        self.time_of_change_fan_speed = 0

    def get_duration(self):
        """
        服务时长，单位为秒
        """
        if self.service_begin_time == -1:
            raise RuntimeError('Not in the service queue')
        return (datetime.datetime.now() - self.service_begin_time).seconds

    def get_ts_duration(self):
        return (datetime.datetime.now() - self.time_slice_begin_time).seconds

    def get_fee(self):
        return round(self.get_duration() * self.fee_rate / 60, 2)

    def save2db(self):
        """
        将一次服务（一条详单条目）持久化到数据库
        """
        # 将 duration 转换为分钟
        request_duration = round(self.get_duration() / 60, 2)
        fee = self.get_fee()
        ServiceModel(room_id=self.room_id,
                     request_time=self.service_begin_time,
                     finish_time=self.service_finish_time,
                     request_duration=request_duration,
                     fan_speed=self.fan_speed,
                     fee_rate=self.fee_rate,
                     fee=fee
                     ).save()

    def __str__(self):
        return '<room_id:' + str(self.room_id) + '\n' + \
               'service_begin_time:' + str(self.service_begin_time) + '\n' + \
               'time_slice_begin_time:' + str(self.time_slice_begin_time) + '\n' + \
               'fan_speed:' + str(self.fan_speed) + '\n' + \
               'target_temp:' + str(self.target_temp) + '\n' + \
               'fee_rate:' + str(self.fee_rate) + '>' + '\n'
