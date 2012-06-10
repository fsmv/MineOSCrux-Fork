#!/usr/bin/python
"""A python script to manage minecraft servers
   Designed for use with MineOS: http://minecraft.codeemo.com
"""

__author__ = "William Dizon"
__license__ = "GNU GPL v3.0"
__version__ = "0.4.12"
__email__ = "wdchromium@gmail.com"

import mineos
import sys

argv = sys.argv

try:
    if argv[1] == 'create':
        mineos.mc(argv[2]).create() 
    elif argv[1] == 'start':
        mineos.mc(argv[2]).start()
    elif argv[1] == 'stop':
        mineos.mc(argv[2]).stop()
    elif argv[1] == 'stopall':
        mineos.mc.stopall()
    elif argv[1] == 'forcestop':
        mineos.mc.forcestop()
    elif argv[1] == 'clean':
        mineos.mc(argv[2]).clean()
    elif argv[1] == 'update':
        mineos.mc.update()
    elif argv[1] == 'update_mineos':
        mineos.mc.update_configs()
        mineos.mc.update_mineos()
    elif argv[1] == 'update_canary':
        mineos.mc(argv[2]).update_canary()
    elif argv[1] == 'backup':
        mineos.mc(argv[2]).backup()
    elif argv[1] == 'backup_status':
        print mineos.mc(argv[2]).status_backup()
    elif argv[1] == 's3fs':
        mineos.mc(argv[2]).s3fs(argv[3])
    elif argv[1] == 'archive':
        mineos.mc(argv[2]).archive()
    elif argv[1] == 'restore':
        mineos.mc(argv[2]).restore()
    elif argv[1] == 'map':
        mineos.mc(argv[2]).mapworld()
    elif argv[1] == 'rename':
        mineos.mc(argv[2]).rename(argv[3])
    elif argv[1] == 'import':
        mineos.mc(argv[2]).importworld(argv[3])
    elif argv[1] == 'backtrack':
        mineos.mc(argv[2]).restore(argv[3], True)
    elif argv[1] == 'import':
        mineos.mc(argv[2]).importworld(argv[3])
    elif argv[1] == 'pigmap':
        mineos.mc(argv[2]).pigmap()
    elif argv[1] == 'pigmap_full':
        mineos.mc(argv[2]).pigmap(True)        
    elif argv[1] == 'say':
        mineos.mc(argv[2]).say(' '.join(argv[3:]))
    elif argv[1] == 'command':
        mineos.mc(argv[2]).command(' '.join(argv[3:]))
    elif argv[1] == 'listplayers':
        players = mineos.mc(argv[2]).list_players()
        print "Current player count: %d" % len(players)
        if players:
            print players

    elif argv[1] == 'listbackups':
        output = mineos.mc(argv[2]).list_backups()
        backup_list = []
        for index, item in enumerate(output):
            count = len(output) - index - 2
            if count < 0 or not index:
                print '{:<4}'.format('') + item
            else:
                print '{:<4}'.format(len(output) - index - 2) + item

    elif argv[1] == 'prune':
        mineos.mc(argv[2]).prune(argv[3])

    elif argv[1] == 'status':
        print mineos.mc(argv[2]).status()

    elif argv[1] == 'listlive':
        print 'Servers located in %s' % mineos.mc().mineos_config['paths']['world_path']
        for server, port, status in mineos.mc().ports_reserved():
            print '{:<15}'.format(server),
            print '{:<10}'.format(port),
            print '{:<10}'.format(status)

    elif argv[1] == 'attribute_list':
        import os
        filename = os.path.join(mineos.mc().mineos_config['paths']['world_path'], argv[2], 'server.properties')
        pairs = mineos.mc.attribute_list(filename)
        for key, value in pairs:
            print key, value

    elif argv[1] == 'list_imports':
        print mineos.mc.list_imports()

    elif argv[1] == 'crontab':
        #./mineos_console.py crontab backup hourly 
        if argv[3] in ['hourly', 'daily', 'weekly', 'monthly']:
            for server in mineos.mc.list_server_frequency(argv[2], argv[3]):
                if argv[2] == 'backup':
                    mineos.mc(server).backup()
                elif argv[2] == 'archive':
                    mineos.mc(server).archive()
                elif argv[2] == 'map':
                    mineos.mc(server).mapworld()
        elif argv[3] == 'reboot':
            for server in mineos.mc.list_server_reboot(argv[2]):
                if argv[2] == 'restore':
                    try:
                        mineos.mc(server).restore('now', True)
                    except mineos.FailedRestoreException:
                        print 'failed restore on %s' % server
                elif argv[2] == 'start':
                    mineos.mc(server).clean()
                    mineos.mc(server).start()           

    elif argv[1] == 'log_archive':
        mineos.mc(argv[2]).log_archive()

except IndexError:
    pass
