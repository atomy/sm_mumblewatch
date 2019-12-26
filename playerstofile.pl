#! /usr/bin/perl

use warnings;
use strict;

open(f_status, "> mumbleusers.txt");

my $home = (getpwuid($<))[7];

if (open(F, "$home/murmur/.dbus.sh")) {
  while(<F>) {
    chomp();
    if ($_ =~ /^(.+?)\='(.+)';$/) {
      $ENV{$1}=$2;
    }
  }
  close(F);
}

use Net::DBus;
use CGI;
use CGI::Carp qw(fatalsToBrowser);

my $q = new CGI;

my $bus;
my $service;

# First try the system bus
eval {
  $bus=Net::DBus->system();
  $service = $bus->get_service("net.sourceforge.mumble.murmur");
};

# If that failed, the session bus
if (! $service) {
  eval {
    $bus = Net::DBus->session();
    $service = $bus->get_service("net.sourceforge.mumble.murmur");
  }
}

die "Murmur service not found" if (! $service);

my $object = $service->get_object("/");
my $servers = $object->getBootedServers();

foreach my $server (@{$servers}) {
  my $name = $object->getConf($server, "registername");
  my $servobj = $service->get_object("/$server");

  # Then, get and print the players
  my $players = $servobj->getPlayers();
  foreach my $p (@{$players}) {
    my @p = @{$p};
    my $chanid = $p[6];
    my $name = $p[8];
    print f_status "$name\n";
  }
}

close f_status;
