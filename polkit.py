import os

import gi
gi.require_version('Polkit', '1.0')
from gi.repository import GObject, Gio, Polkit

TIMEOUT = 10*1000 #10 seconds

def _on_timeout(loop):
    loop.quit()
    return False

def _on_cancel(cancellable):
    cancellable.cancel()
    return False

def execute(func, *args, **kwargs):

    def check_authorization_cb(authority, res, loop):
        try:
            result = authority.check_authorization_finish(res)
            if result.get_is_authorized():
                # execute
                func(*args, **kwargs)
            elif result.get_is_challenge():
                print("Challenge")
            else:
                print("Not authorized")
        except GObject.GError as error:
             print("Error checking authorization: %s" % error.message)

        loop.quit()



    mainloop = GObject.MainLoop()
    authority = Polkit.Authority.get()
    subject = Polkit.UnixProcess.new(os.getppid())

    cancellable = Gio.Cancellable()
    GObject.timeout_add(TIMEOUT, _on_cancel, cancellable)

    authority.check_authorization(subject,
        "org.freedesktop.policykit.exec",
        None,
        Polkit.CheckAuthorizationFlags.ALLOW_USER_INTERACTION,
        cancellable,
        check_authorization_cb,
        mainloop)

    mainloop.run()
