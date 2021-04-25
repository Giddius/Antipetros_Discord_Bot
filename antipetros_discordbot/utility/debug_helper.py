import platform


def show_toast(title: str, msg: str, duration: int = 5):
    if platform.system().casefold() != 'windows':
        print(title, msg, str(duration))
        return
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    toaster.show_toast(title=title, msg=msg, duration=duration)
