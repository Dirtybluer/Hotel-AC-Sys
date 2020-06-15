from datetime import datetime

from django.http import JsonResponse

from Management.controller import Controller


def power_on(request):
    controller = Controller()
    controller.settings['mode'] = eval(request.POST.get('mode'))
    controller.settings['tempHighLimit'] = eval(request.POST.get('tempHighLimit'))
    controller.settings['tempLowLimit'] = eval(request.POST.get('tempLowLimit'))
    controller.settings['defaultTargetTemp'] = eval(request.POST.get('defaultTargetTemp'))
    controller.settings['FeeRateH'] = eval(request.POST.get('FeeRateH'))
    controller.settings['FeeRateM'] = eval(request.POST.get('FeeRateM'))
    controller.settings['FeeRateL'] = eval(request.POST.get('FeeRateL'))
    controller.print_log()
    return JsonResponse({'msg': 'OK'})


def check_room_state(request):
    controller = Controller()
    room_state = controller.get_room_state()
    controller.print_log()
    return JsonResponse(room_state, safe=False)


def check_RDR(request):
    controller = Controller()
    date_in = datetime.strptime(request.POST.get('dateIn'), "%Y-%m-%d %H:%M")
    date_out = datetime.strptime(request.POST.get('dateOut'), "%Y-%m-%d %H:%M")

    DRD = controller.get_DRD(date_in, date_out)
    controller.print_log()
    return JsonResponse(DRD, safe=False)


def check_bill(request):
    room_id = eval(request.POST.get('roomId'))
    date_in = datetime.strptime(request.POST.get('dateIn'), "%Y-%m-%d %H:%M")
    date_out = datetime.strptime(request.POST.get('dateOut'), "%Y-%m-%d %H:%M")

    controller = Controller()
    total_fee = controller.get_bill(date_in, date_out)

    controller.print_log()

    return JsonResponse({
        'roomId': room_id,
        'totalFee': total_fee,
        'dateIn': request.POST.get('dateIn'),
        'dateOut': request.POST.get('dateOut')
    })


def check_report(request):
    print(type(request.POST.get('date')))
    date = datetime.strptime(request.POST.get('date'), "%Y-%m-%d")
    report_type = eval(request.POST.get('typeReport'))
    controller = Controller()
    report = controller.get_report(date, report_type)
    controller.print_log()
    return JsonResponse(report, safe=False)
