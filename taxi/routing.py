# Third-party imports.
from channels import route_class

# Local imports.
from trip.consumers import DriverConsumer, RiderConsumer


channel_routing = [
    route_class(DriverConsumer, path=r'^/driver/$'),
    route_class(RiderConsumer, path=r'^/rider/$'),
]
