#!/usr/bin/env python

from prometheus_client import start_http_server, Counter, Gauge
import os
import json
import yaml
import sys
import requests
import signal
import time
from sims.loadbalancersim import LoadBalancerSim as new_lb


class SimulateLoadBalancing(object):
    kill_now = False

    def __init__(self, config_dict, debug=False):
        try:
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)
            self.load_balancers = []
            self.config_dict = yaml.load(config_dict, Loader=yaml.FullLoader)
            self.lb_metrics = Gauge('load_balancer_sims', 'Service Level Counters',
                                    ['uuid', 'active'])
            self.is_running = True
            self.reset_dictionary = {}
            self.load_balancers_left = 0
            self.max_connections = {"server_count": 0, "conn_count": 0}
            self.starting_conns = 0
        except (KeyboardInterrupt, SystemExit):
            sys.exit(1)

    def exit_gracefully(self, signum, frame):
        """
        :param signum: Linux Signal
        :param frame: Linux Frame
        :return:
        """
        print("Closing down...")
        self.kill_now = True
        sys.exit(1)

    def load_config(self, config):
        """
        :param config: This is the dictionary time that will reference the part of the tests
        """
        connections_per = round(self.config_dict['tests'][config]['connections'] / self.config_dict['tests'][config]['loadbalancercount'])
        self.starting_conns = connections_per
        for i in range(self.config_dict['tests'][config]['loadbalancercount']):
            self.load_balancers.append(new_lb(connections_per))

    def run(self):
        """

        """
        tests = self.config_dict['tests'].keys()
        for test in tests:
            self.load_config(test)
            for t in range(self.config_dict['tests'][test]['times']):
                reset_dict = self.run_test(test)
                self.update_max(reset_dict)
                self.is_running = True
                self.reset_dictionary = {}
            print("########################################")
            print("NEW TEST RESULTS")
            print("Results of test {} after {} resets".format(test, self.config_dict['tests'][test]['times'] ))
            print("Max Conns: {}".format(self.max_connections['conn_count']))
            print("Max Servers with Conns: {}".format(self.max_connections['server_count']))
            print("Starting connections per: {}".format(self.starting_conns))
            print("Percent Increase on Conntions: {}%".format(round(self.max_connections['conn_count']/self.starting_conns*100)))
            print("########################################")
            print("########################################")
            print("########################################")
        self.exit_gracefully(1,1)

    def run_test(self,config):
        reset_dict = {"server_count": 0, "conn_count": 0}
        while self.is_running:
            self.reset_loadbalancers(self.config_dict['tests'][config]['resetratio'])
            self.reset_again()
            self.update_prom_stats()
        return reset_dict
    def update_prom_stats(self):
        if len(self.load_balancers) > 0:
            for lb in self.load_balancers:
                self.lb_metrics.labels(uuid=lb.get_uuid(), active=lb.isactive()).set(int(lb.get_connections()))

    def update_max(self, reset_dict):
        if reset_dict['conn_count'] > self.max_connections['conn_count']:
            self.max_connections['conn_count'] = reset_dict['conn_count']
            self.max_connections['server_count'] = reset_dict['server_count']

    def reset_loadbalancers(self, ratio):
        conns_distribution = 0
        new_ratio = self.get_ration(ratio)
        last_run = False
        reset_count = 0
        if new_ratio != ratio:
            last_run = True
        for r in range(new_ratio):
            for i in self.load_balancers:
                if (not self.reset_dictionary.get(i.get_uuid()) and i.isactive):
                    conns_distribution += i.reset_load_balancer()
                    self.reset_dictionary[i.get_uuid()] = True
                    new_ratio -= 1
                    reset_count += 1
                if new_ratio == 0:
                    break
        if reset_count == 0:
            divisor = 1
        else:
            divisor = reset_count
        if round(conns_distribution/divisor) > self.max_connections['conn_count']:
            self.max_connections = {"server_count": reset_count, "conn_count": round(conns_distribution/divisor)}
        self.distribute_load(self.get_active_lb_count(), conns_distribution)
        self.activate_lbs()

    def get_ration(self, ratio):
        remaining = len(self.load_balancers) - len(self.reset_dictionary.keys())
        if ratio > remaining:
            return remaining
        return ratio

    def get_active_lb_count(self):
        active_lbs = 0
        for i in self.load_balancers:
            if i.isactive():
                active_lbs += 1
        return active_lbs

    def distribute_load(self, active_lbs, conns):
        conns_to_dist = round(conns/active_lbs)
        for i in self.load_balancers:
            if i.isactive():
                i.add_connections(conns_to_dist)

    def activate_lbs(self):
        for i in self.load_balancers:
            i.set_active()

    def reset_again(self):
        self.is_running = len(self.load_balancers) != len(self.reset_dictionary.keys())


if __name__ == '__main__':
    try:
        start_http_server(8000)
    except:
        print("Env not set correctly please check.")
        sys.exit(1)
    f = open("./load_balancing.yaml", "r")
    sim = SimulateLoadBalancing(f)
    while not sim.kill_now:
        sim.run()
        time.sleep(300)
