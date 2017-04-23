# Standard library imports.

# Django imports.

# Third-party imports.
from channels import route_class

# Local imports.
from trip.consumers import TripConsumer


channel_routing = [
    route_class(TripConsumer, path=r'^/status/$'),
]
