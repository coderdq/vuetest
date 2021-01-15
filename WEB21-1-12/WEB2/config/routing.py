from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import t2kmodule.routing
import t2kmachine.routing
import lvboqi.routing
import power.routing
import tempcomp.routing

application=ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            t2kmachine.routing.websocket_urlpatterns
            +lvboqi.routing.websocket_urlpatterns
            +power.routing.websocket_urlpatterns
            +t2kmodule.routing.websocket_urlpatterns
            +tempcomp.routing.websocket_urlpatterns
        )
    ),
})