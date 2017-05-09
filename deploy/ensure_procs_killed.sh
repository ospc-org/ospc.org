#!/usr/bin/env bash

kill_from_args(){
    if [ "$1" = "" ];then
        echo Do nothing - give an arg like \"flask\" or \"celery\";
        return 1;
    fi
    ps aux | grep "$1"  | grep 'python' | awk -F' ' '{print $2}' | xargs -n 1 kill -9;
}
kill_from_args $1


