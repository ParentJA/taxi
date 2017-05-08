from channels import route_class
from trip.consumers import DriverConsumer, RiderConsumer


channel_routing = [
    route_class(DriverConsumer, path=r'^/driver/$'),
    route_class(RiderConsumer, path=r'^/rider/$'),
]
