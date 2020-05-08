#!/usr/bin/env python
import copy
import uuid


class LoadBalancerSim(object):

    def __init__(self, connections, debug=False):
        try:
            self.connections = connections
            self.active = True
            self.uuid = uuid.uuid4()

        except (KeyboardInterrupt, SystemExit):
            sys.exit(1)

    def exit_gracefully(self, signum, frame):
        print("Closing down...")
        self.kill_now = True
        sys.exit(1)

    def add_connections(self, connections):
        self.connections += connections
        return

    def reset_load_balancer(self):
        current_connections = copy.deepcopy(self.connections)
        self.connections = 0
        self.active = False
        return current_connections

    def isactive(self):
        return self.active

    def set_active(self):
        self.active = True
        return self.active

    def get_uuid(self):
        return self.uuid

    def get_connections(self):
        return self.connections


def main():
    lb = LoadBalancerSim(10)
    return print("{}".format(lb.isactive()))


if __name__ == "__main__":
    main()
