default: all

all: listenmumblesig.c
	gcc -I /usr/lib/dbus-1.0/include/ -I /usr/include/dbus-1.0/ listenmumblesig.c -o listenmumblesig `pkg-config --libs dbus-1 glib-2.0 dbus-glib-1`
