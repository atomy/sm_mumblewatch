/*
 * Listen for mumble signals on d-bus
 * Written by atomy <atomy@jackinpoint.net>
 */
#include <dbus/dbus.h>
#include <stdbool.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <errno.h>

DBusConnection* conn;
DBusError err;

int dbus_conn()
{
	int ret;

	dbus_error_init(&err);

	conn = dbus_bus_get(DBUS_BUS_SYSTEM, &err);

	if (dbus_error_is_set(&err))
	{
		fprintf(stderr, "connection error (%s)\n", err.message);
		dbus_error_free(&err);
		return 1;
	}
	else if (conn == NULL)
	{
		fprintf(stderr, "connection is NULL, but no error-message available\n");
		return 1;
	}
	else
	{
		fprintf(stdout, "connection succeeded\n");
	}

	ret = dbus_bus_request_name(conn, "gameserver.srcds.mumble.watch", DBUS_NAME_FLAG_REPLACE_EXISTING, &err);

	if (dbus_error_is_set(&err))
	{
		fprintf(stderr, "name error (%s)\n", err.message);
		dbus_error_free(&err);
		return 1;
	}
	else if (DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER != ret)
	{
		fprintf(stderr, "name error - no error msg\n");
		return 1;
	}
	else
	{
		fprintf(stdout, "got the bus\n");
	}

	return 0;
}

/**
 * Call a method on a remote object
 */
void query(char* param) 
{
	DBusMessage* msg;
   	DBusMessageIter args;
   	DBusPendingCall* pending;
   	bool stat;
   	dbus_uint32_t level;

   	// create a new method call and check for errors
   	msg = dbus_message_new_method_call("net.sourceforge.mumble.Murmur", // target for the method call
        				"/1", // object to call on - its the servid of murmur, we want only one of it
                                      	"net.sourceforge.mumble.Murmur", // interface to call on
                                      	"getPlayers"); // method name
  	if (msg == NULL) 
   	{ 
      		fprintf(stderr, "Message Null\n");
      		exit(1);
   	}

  	// append arguments
   	dbus_message_iter_init_append(msg, &args);
   	if (!dbus_message_iter_append_basic(&args, DBUS_TYPE_STRING, &param)) 
	{
      		fprintf(stderr, "Out Of Memory!\n"); 
      		exit(1);
   	}
   
   	// send message and get a handle for a reply
   	if (!dbus_connection_send_with_reply (conn, msg, &pending, -1)) 
	{ // -1 is default timeout
      		fprintf(stderr, "Out Of Memory!\n"); 
      		exit(1);
   	}

   	if (NULL == pending) 
	{ 
      		fprintf(stderr, "Pending Call Null\n"); 
      		exit(1); 
   	}
   	
	dbus_connection_flush(conn);
   
   	printf("Request Sent\n");
   
   	// free message
   	dbus_message_unref(msg);
   
   	// block until we recieve a reply
  	dbus_pending_call_block(pending);

   	// get the reply message
   	msg = dbus_pending_call_steal_reply(pending);
   	
	if (NULL == msg) 	
	{
     		fprintf(stderr, "Reply Null\n"); 
      		exit(1); 
   	}
   	
	// free the pending message handle
   	dbus_pending_call_unref(pending);

   	// read the parameters
   	if (!dbus_message_iter_init(msg, &args))
      		fprintf(stderr, "Message has no arguments!\n"); 
   	else if (DBUS_TYPE_BOOLEAN != dbus_message_iter_get_arg_type(&args)) 
      		fprintf(stderr, "Argument is not boolean!\n"); 
   	else
      		dbus_message_iter_get_basic(&args, &stat);

   	if (!dbus_message_iter_next(&args))
      		fprintf(stderr, "Message has too few arguments!\n"); 
   	else if (DBUS_TYPE_UINT32 != dbus_message_iter_get_arg_type(&args)) 
      		fprintf(stderr, "Argument is not int!\n"); 
   	else
      		dbus_message_iter_get_basic(&args, &level);

   	printf("Got Reply: %d, %d\n", stat, level);
   
   	// free reply 
   	dbus_message_unref(msg);   
}

void reply_to_method_call(DBusMessage* msg, DBusConnection* conn)
{
   DBusMessage* reply;
   DBusMessageIter args;
   bool stat = true;
   dbus_uint32_t level = 21614;
   dbus_uint32_t serial = 0;
   char* param = "";

   // read the arguments
   if (!dbus_message_iter_init(msg, &args))
      fprintf(stderr, "Message has no arguments!\n"); 
   else if (DBUS_TYPE_STRING != dbus_message_iter_get_arg_type(&args)) 
      fprintf(stderr, "Argument is not string!\n"); 
   else 
      dbus_message_iter_get_basic(&args, &param);

   printf("Method called with %s\n", param);

   // create a reply from the message
   reply = dbus_message_new_method_return(msg);

   // add the arguments to the reply
   dbus_message_iter_init_append(reply, &args);
   if (!dbus_message_iter_append_basic(&args, DBUS_TYPE_BOOLEAN, &stat)) { 
      fprintf(stderr, "Out Of Memory!\n"); 
      exit(1);
   }
   if (!dbus_message_iter_append_basic(&args, DBUS_TYPE_UINT32, &level)) { 
      fprintf(stderr, "Out Of Memory!\n"); 
      exit(1);
   }

   // send the reply && flush the connection
   if (!dbus_connection_send(conn, reply, &serial)) {
      fprintf(stderr, "Out Of Memory!\n"); 
      exit(1);
   }
   dbus_connection_flush(conn);

   // free the reply
   dbus_message_unref(reply);
}

void action()
{
	pid_t cpid;
	int childExitStatus;
       
       	cpid = fork();

	if (cpid == 0)
	{
                if (execl("/usr/bin/perl", "/usr/bin/perl", "playerstofile.pl", (char *)NULL) < 0)
		                        fprintf(stderr, "err: %s\n", strerror(errno));
	
		exit(0);
	}
        
	waitpid(cpid, &childExitStatus, WCONTINUED);

        cpid = fork();

        if (cpid == 0)
        {
                if (execl("/usr/bin/python", "/usr/bin/python", "rcon_checkmumbleplayers.py", (char *)NULL) < 0)
                        fprintf(stderr, "err: %s\n", strerror(errno));

                exit(0);
        }

        waitpid(cpid, &childExitStatus, WCONTINUED);

}

/**
 * Server that exposes a method call and waits for it to be called
 */
void listen() 
{
   DBusMessage* msg;
   DBusMessage* reply;
   DBusMessageIter args;
   DBusConnection* conn;
   DBusError err;
   int ret;
   char* param;

   printf("Listening for method calls\n");

   // initialise the error
   dbus_error_init(&err);
   
   // connect to the bus and check for errors
   conn = dbus_bus_get(DBUS_BUS_SESSION, &err);
   if (dbus_error_is_set(&err)) { 
      fprintf(stderr, "Connection Error (%s)\n", err.message); 
      dbus_error_free(&err); 
   }
   if (NULL == conn) {
      fprintf(stderr, "Connection Null\n"); 
      exit(1); 
   }
   
   // request our name on the bus and check for errors
   ret = dbus_bus_request_name(conn, "test.method.server", DBUS_NAME_FLAG_REPLACE_EXISTING , &err);
   if (dbus_error_is_set(&err)) { 
      fprintf(stderr, "Name Error (%s)\n", err.message); 
      dbus_error_free(&err);
   }
   if (DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER != ret) { 
      fprintf(stderr, "Not Primary Owner (%d)\n", ret);
      exit(1); 
   }

   // loop, testing for new messages
   while (true) {
      // non blocking read of the next available message
      dbus_connection_read_write(conn, 0);
      msg = dbus_connection_pop_message(conn);

      // loop again if we haven't got a message
      if (NULL == msg) { 
         sleep(1); 
         continue; 
      }
      
      // check this is a method call for the right interface & method
      if (dbus_message_is_method_call(msg, "test.method.Type", "Method")) 
         reply_to_method_call(msg, conn);

      // free the message
      dbus_message_unref(msg);
   }

}

/**
 * Listens for signals on the bus
 */
void receive()
{
	DBusMessage* msg;
   	DBusMessageIter args;
   	int ret;
   	char* sigvalue;

   	printf("Listening for signals\n");

   	// initialise the errors
   	dbus_error_init(&err);
   
   	// connect to the bus and check for errors
   	conn = dbus_bus_get(DBUS_BUS_SYSTEM, &err);
   
   	if (dbus_error_is_set(&err)) 
	{ 
      		fprintf(stderr, "Connection Error (%s)\n", err.message);
      		dbus_error_free(&err); 
   	}
   
   	if (NULL == conn) 
	{ 
      		exit(1);
   	}
   
   	// request our name on the bus and check for errors
   	ret = dbus_bus_request_name(conn, "gameserver.srcds.mumble.watch", DBUS_NAME_FLAG_REPLACE_EXISTING , &err);

   	if (dbus_error_is_set(&err)) 
	{ 
      		fprintf(stderr, "Name Error (%s)\n", err.message);
      		dbus_error_free(&err); 
	}
   
   	if (DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER != ret) 
	{
      		exit(1);
  	}

   	/*
    	* add a rule for connecting and leaving players
    	*/
   	dbus_bus_add_match(conn, "type='signal',interface='net.sourceforge.mumble.Murmur',member='playerDisconnected'", &err);
   	dbus_bus_add_match(conn, "type='signal',interface='net.sourceforge.mumble.Murmur',member='playerConnected'", &err);
   	dbus_connection_flush(conn);

   	if (dbus_error_is_set(&err)) 
	{ 
      		fprintf(stderr, "Match Error (%s)\n", err.message);
      		exit(1); 
   	}
   	printf("Match rule sent\n");

   	// loop listening for signals being emmitted
   	while (true) 
	{

      		// non blocking read of the next available message
      		dbus_connection_read_write(conn, 0);
      		msg = dbus_connection_pop_message(conn);

      		// loop again if we haven't read a message
      		if (NULL == msg) 
		{ 
         		sleep(1);
         		continue;
      		}

      		if (strncmp(dbus_message_get_interface(msg), "net.sourceforge.mumble.Murmur", 255) == 0)
		{
	   			if (strncmp(dbus_message_get_member(msg), "playerConnected", 255) == 0)
	   			{
					action();
					printf("player connected\n");
				}
				else if (strncmp(dbus_message_get_member(msg), "playerDisconnected", 255) == 0)
				{		
					action();
					printf("player disconnected\n");
				}
		}
	}
      
      	// free the message
      	dbus_message_unref(msg);
}

int main(int argc, char** argv)
{
	//dbus_conn();
	receive();
}
