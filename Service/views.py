import json

from django.http import JsonResponse

from Management.controller import Controller, Service


def request_on(request):
    controller = Controller()
    data = json.loads(request.body)
    print(data.get('mode'))
    room_id = data.get('roomId')
    mode = data.get('mode')
    target_temp = controller.settings['defaultTargetTemp']
    controller.update_room_temp(room_id, data.get('currentRoomTemp'))
    service = Service(room_id=room_id, mode=mode, target_temp=target_temp)
    result = controller.request_on(service)

    response = {
        'statue': result,
        'message': {
            'mode': service.mode,
            'targetTemp': service.target_temp,
            'fan': service.fan_speed,
            'fee': controller.get_room_fee(room_id),
            'feeRate': service.fee_rate,
        }
    }
    controller.print_log()
    return JsonResponse(response)


def change_target_temp(request):
    controller = Controller()
    data = json.loads(request.body)
    room_id = data.get('roomId')
    target_temp = data.get('targetTemp')
    controller.change_target_temp(room_id, target_temp)
    controller.print_log()
    return JsonResponse({'msg': 'OK'})


def change_fan_speed(request):
    controller = Controller()
    data = json.loads(request.body)

    room_id = data.get('roomId')
    fan_speed = data.get("fanSpeed")
    controller.change_fan_speed(room_id, fan_speed)

    if fan_speed == 1:
        response = {"feeRate": controller.settings['FeeRateL']}
    elif fan_speed == 2:
        response = {"feeRate": controller.settings['FeeRateM']}
    elif fan_speed == 3:
        response = {"feeRate": controller.settings['FeeRateH']}
    else:
        raise RuntimeError('No such speed')

    controller.print_log()
    return JsonResponse(response)


def request_off(request):
    controller = Controller()
    data = json.loads(request.body)

    room_id = data.get('roomId')
    controller.request_off(room_id)
    controller.print_log()
    return JsonResponse({'msg': 'OK'})


def request_info(request):
    """
    接收房间状态。
    1. 更新房间的室温
    2. 获取房间空调状态
        - "3"：达到目标温度
        - "4"：达到温度阈值，继续服务
        - "大于4"： 正在回温度
    """
    controller = Controller()
    data = json.loads(request.body)

    room_id = data.get('roomId')
    statue = data.get('statue')
    current_temp = data.get('currentTemp')
    controller.update_room_temp(room_id, current_temp)
    if statue == 3:
        controller.pause_service(room_id)
    elif statue == 4:
        controller.resume_service(room_id)
    controller.print_log()
    return JsonResponse({
        'statue': controller.room_state[room_id]['AC_status'],
        'fee': controller.get_room_fee(room_id)
    })

