#!/usr/bin/python
"""A python script to manage minecraft servers
   Designed for use with MineOS: http://minecraft.codeemo.com
"""

__author__ = "William Dizon"
__license__ = "GNU GPL v3.0"
__version__ = "0.4.11b"
__email__ = "wdchromium@gmail.com"

import os
import ConfigParser
import subprocess
import shlex
import time
import logging

logfile = '/usr/games/minecraft/mineos.log'
try:
    logging.basicConfig(filename=logfile,level=logging.DEBUG)
except:
    logging.basicConfig(level=logging.DEBUG)

class mc:
    mc_path = ''
    canary_extracts = ['CanaryMod.jar', 'rules.rules', 'jarjar.jar', 'mysql-connector-java-bin.jar', 'minecraft.sql', 'update-b7.sql', 'update-b8.sql']
    #version.txt left out for tainted mode

    def __init__(self, server_name=None):
        self.server_name = server_name
        if os.access('mineos.config', os.R_OK):
            #logging.debug('(%s) local mineos.config: OK', self.server_name)
            self.mineos_config = mc.config_import('mineos.config')
            self.mc_path = self.mineos_config['paths']['mc_path']
            mc.mc_path = self.mc_path
        elif os.access(os.path.join(mc.mc_path, 'mineos.config'), os.R_OK):
            self.mineos_config = mc.config_import(os.path.join(mc.mc_path, 'mineos.config'))
            self.mc_path = self.mineos_config['paths']['mc_path']
        else:
            logging.critical('(%s) mineos.config not found in present working directory--unable to continue', self.server_name)
            raise ConfigNotFoundException
            
        if self.mineos_config and server_name:
            self.cwd = os.path.join(self.mineos_config['paths']['world_path'], server_name)
            self.bwd = os.path.join(self.mineos_config['paths']['backup_path'], server_name)
            self.awd = os.path.join(self.mineos_config['paths']['archive_path'], server_name)
            self.swd = os.path.join(self.mineos_config['paths']['snapshot_path'], server_name)
            self.pwd = os.path.join(self.cwd, 'plugins')

            self.sp = os.path.join(self.cwd, 'server.properties')
            self.sc = os.path.join(self.cwd, 'server.config')
            
            try:
                snapshotpath = self.mineos_config['paths']['http_snapshot_path']
            except KeyError:
                snapshotpath = '/var/www/hiawatha/pigmap'
                mc.config_add(os.path.join(self.mc_path, 'mineos.config'), 'paths', 'http_snapshot_path', snapshotpath, self.server_name)
                if not os.path.exists(snapshotpath): os.makedirs(snapshotpath)
            finally:
                self.mwd = os.path.join(snapshotpath, server_name)
            
            self.server_config = mc.config_import(os.path.join(self.cwd, 'server.config'))

    def status(self):
        def check_sanity():
            sanity = {}
            sanity['cwd'] = os.path.exists(self.cwd)
            sanity['bwd'] = os.path.exists(self.bwd)
            sanity['awd'] = os.path.exists(self.awd)
            sanity['swd'] = os.path.exists(self.swd)
            sanity['pwd'] = os.path.exists(self.pwd)
            sanity['mwd'] = os.path.exists(self.mwd)

            sanity['server_properties'] = os.access(os.path.join(self.cwd, 'server.properties'), os.W_OK)
            sanity['server_config'] = os.access(os.path.join(self.cwd, 'server.config'), os.W_OK)
            sanity['server_log_lck'] = os.access(os.path.join(self.cwd, 'server.log.lck'), os.W_OK)
            sanity['session_lock'] = os.access(os.path.join(self.cwd,
                                                            mc.attribute_find(os.path.join(self.cwd, 'server.properties'), 'level-name', self.server_name) or 'world',
                                                            'session.lock'),
                                               os.W_OK)     
            return sanity
        
        self.sanity = check_sanity()
        if self.sanity['cwd']:
            if self.sanity['server_log_lck'] and self.sanity['session_lock']:
                logging.info('(%s) lock files: 2 of 2', self.server_name)
                return 'up'
            if self.sanity['server_log_lck'] ^ self.sanity['session_lock']:
                logging.warning('(%s) lock files: 1 of 2--unclean world tree', self.server_name)
                return 'unclean'
            if self.sanity['server_properties'] and not self.sanity['server_config']:
                logging.info('(%s) lock files: 0 of 0, server.properties: found, server.config: none', self.server_name)
                return 'foreign'
            if self.sanity['server_properties'] and self.sanity['server_config']:
                logging.info('(%s) lock files: 0 of 2: OK', self.server_name)
                return 'down'
            if not self.sanity['server_properties'] and self.sanity['server_config']:
                logging.info('(%s) lock files: 0 of 0, server.properties: none, server.config: found', self.server_name)
                return 'template'
            logging.warning('(%s) lock files: 0 of 0, server.properties: none, server.config: none', self.server_name)
            return 'empty'
        logging.error('(%s) working directory does not exist', self.server_name)
        return 'not-found'

    def status_backup(self):
        self.bwd = os.path.join(self.mineos_config['paths']['backup_path'], self.server_name)
        if os.path.exists(self.bwd):
            if os.access(os.path.join(self.bwd, 'server.log.lck'), os.F_OK) or \
               os.access(os.path.join(self.bwd,
                                      mc.attribute_find(os.path.join(self.bwd, 'server.properties'), 'level-name', self.server_name) or 'world',
                                      'session.lock'),
                         os.F_OK):
                logging.warning('(%s) backup directory lock files: found', self.server_name)
                return 'unclean'
            if os.access(os.path.join(self.bwd, 'server.properties'), os.W_OK):
                logging.info('(%s) backup directory OK', self.server_name)
                return 'found'
            logging.error('(%s) backup directory empty', self.server_name)
            return 'empty'
        logging.error('(%s) backup directory does not exist', self.server_name)
        return 'not-found'

    @staticmethod
    def update_mineos():
        logging.info('(None) <update_mineos>')
        
        filename = 'update.sh'
        update_url = 'http://minecraft.codeemo.com/crux/mineos-scripts/%s' % filename
                
        mc.check(filename, update_url)

        mc_path = mc().mc_path
        os.chdir(mc_path)
        os.chmod(os.path.join(mc_path, filename), 0755)
        
        execute_command = os.path.join(mc_path, 'update.sh')
        logging.info('%s', execute_command)
        output = subprocess.check_output(shlex.split(execute_command))
        print '(MineOS) update complete.' 

    @staticmethod
    def check(filename, url):
        import shutil, hashlib, urllib
        
        def md5sum(filepath):
            infile = open(os.path.join(filepath), 'rb')
            content = infile.read()
            infile.close()
            m = hashlib.md5()
            m.update(content)
            md5 = m.hexdigest()
            return md5

        mc_path = mc().mc_path
        os.chdir(mc_path)
        logging.debug('%s', 'downloading %s' % filename)

        urllib.urlretrieve(url, filename + '.new')

        oldfile = os.path.join(mc_path, filename)
        newfile = os.path.join(mc_path, filename + '.new')           

        if os.access(newfile, os.R_OK):
            if os.access(oldfile, os.W_OK):
                logging.info('(None) md5sum %s.new: %s', filename, md5sum(newfile))
                logging.info('(None) md5sum %s    : %s', filename, md5sum(oldfile))
                if md5sum(newfile) != md5sum(oldfile):
                    logging.info('(None) new %s kept', newfile)
                    shutil.move(newfile, oldfile)
                else:
                    logging.info('(None) existing %s kept', oldfile)
                    os.unlink(newfile)
            else:
                logging.info('(None) %s does not exist, keeping %s', filename, newfile)
                shutil.move(newfile, oldfile)
        else:
            logging.error('(None) download failed: %s', url)
            raise DownloadFailedException

    @staticmethod
    def updatesingle(mod):
        logging.info('(None) <updatesingle> %s', mod)

        instance = mc()
        for k, path in instance.mineos_config['paths'].items():
            try:
                if not os.path.exists(path): os.makedirs(path)
            except:
                logging.warning('(None) unable to create directory %s', path)
                
        if mod == 'pure':
            mc.check(instance.mineos_config['downloads']['mc_jar'], instance.mineos_config['downloads']['mc_jarloc'])

        elif mod == 'bukkit':
            mc.check(instance.mineos_config['downloads']['bukkit_jar'], instance.mineos_config['downloads']['bukkit_jarloc'])

        elif mod == 'canary':
            import zipfile
            filepath = os.path.join(instance.mc_path, instance.mineos_config['downloads']['canary_zip'])
            filename = instance.mineos_config['downloads']['canary_zip']
            mc.check(filename, instance.mineos_config['downloads']['canary_ziploc'])

            try:
                cpath = os.path.join(instance.mc_path, 'canary')
                if not os.path.exists(cpath): os.makedirs(cpath)
            except:
                logging.warning('(None) unable to create directory %s', cpath)

            if zipfile.is_zipfile(filepath):
                try:
                    with zipfile.ZipFile(filepath, mode='r') as zipchive:
                        zipchive.extractall(os.path.join(instance.mc_path, 'canary'))
                        logging.info('(None) All canarymod files extracted from %s.' % filename)
                except:
                    raise ArchiveUnexpectedException('None', filename)

        elif mod == 'c10t':
            import tarfile
            mc.check(instance.mineos_config['downloads']['c10t_tgz'], instance.mineos_config['downloads']['c10t_tgzloc'])
            
            if not os.path.isdir(os.path.join(instance.mc_path, instance.mineos_config['downloads']['c10t_tgz'][:-7:])):
                filename = os.path.join(instance.mc_path, instance.mineos_config['downloads']['c10t_tgz'])

                try:
                    if tarfile.is_tarfile(filename):
                        logging.info('(None) %s is a valid tarfile, opening...', filename)
                        tarfile.open(filename, mode='r:gz').extractall(instance.mc_path)
                        logging.info('(None) %s extracted.' % filename)
                except:
                    raise TarNotExtractingException

            try:
                if not os.access(os.path.join(instance.mc_path, 'c10t'), os.F_OK):
                    logging.info('(None) creating symlink: %s', os.path.join(instance.mc_path, 'c10t'))
                    os.symlink(os.path.join(instance.mc_path, instance.mineos_config['downloads']['c10t_tgz'][:-7:]), \
                               os.path.join(instance.mc_path, 'c10t'))
            except:
                logging.error('(None) unable to create symlink: %s', os.path.join(instance.mc_path, 'c10t'))

    @staticmethod
    def update():
        logging.info('(None) <update>')

        instance = mc()
        if instance.mineos_config['update']['pure'] == 'true':
            mc.updatesingle('pure')
        if instance.mineos_config['update']['bukkit'] == 'true':
            mc.updatesingle('bukkit')
        if instance.mineos_config['update']['canary'] == 'true':
            mc.updatesingle('canary')
        if instance.mineos_config['update']['c10t'] == 'true':
            mc.updatesingle('c10t')

        print '(MineOS) update server files complete.'

    def update_canary(self):
        import distutils.dir_util
            
        try:
            distutils.dir_util.copy_tree(os.path.join(self.mc_path, 'canary'), self.cwd)
            logging.info('(None) canary tree copied to %s' % self.cwd)
        except:
            raise GenericException(self.server_name, 'copying canary dependencies') 

    def createdirs(self):
        for coredir in [self.cwd, self.bwd, self.awd, self.swd, self.pwd]:
            try:
                os.makedirs(coredir)
            except OSError:
                pass
                    
    def create(self, arguments={}):
        logging.info('(%s) <create>', self.server_name)
        if not self.server_name:
            logging.critical('(%s) all servers must have a name', self.server_name)
            raise InvalidServerNameError()
        if ' ' in self.server_name or "'" in self.server_name:
            logging.critical('(%s) server may not have spaces or non-alphanumerics', self.server_name)
            raise InvalidServerNameError()        

        DEFAULT_MEM = '1024'
        DEFAULT_PORT = '25565'
        DEFAULT_MAX_PLAYERS = '20'
        DEFAULT_ARCHIVE = 'none'
        DEFAULT_BACKUP = 'none'
        DEFAULT_MAP = 'none'
        
        status = self.status()

        if status in ['not-found', 'empty', 'foreign']:
            self.createdirs()

            try:
                if int(arguments['port']) <= 1024:
                    arguments['port'] = DEFAULT_PORT
            except:
                arguments['port'] = DEFAULT_PORT

            try:
                if int(arguments['mem']) < 256:
                    arguments['mem'] = '256'
            except:
                arguments['mem'] = DEFAULT_MEM

            try:
                if int(arguments['max_players']) < 1:
                    arguments['max_players'] = '1'
            except:
                arguments['max_players'] = DEFAULT_MAX_PLAYERS
            
            config = ConfigParser.SafeConfigParser(allow_no_value=True)

            config.add_section("minecraft")
            config.set("minecraft", "port", arguments.get('port', DEFAULT_PORT))
            config.set("minecraft", "max_players", arguments.get('max_players', DEFAULT_MAX_PLAYERS))
            config.set("minecraft", "mem", arguments.get('mem', DEFAULT_MEM))
            config.set("minecraft", "level_seed", arguments.get('level_seed', ''))
            config.set("minecraft", "gamemode", arguments.get('gamemode', ''))
            config.set("minecraft", "difficulty", arguments.get('difficulty', ''))

            config.add_section("crontabs")
            config.set("crontabs", "freq_archive", arguments.get('freq_archive', DEFAULT_ARCHIVE))
            config.set("crontabs", "freq_backup", arguments.get('freq_backup', DEFAULT_BACKUP))
            config.set("crontabs", "freq_map", arguments.get('freq_map', DEFAULT_MAP))

            config.add_section("onreboot")
            config.set("onreboot", "restore", arguments.get('restore', 'false'))
            config.set("onreboot", "start", arguments.get('start', 'false'))

            config.add_section("mapping")
            config.set("mapping", "map_standard", 'true')
            config.set("mapping", "map_caves", 'true')
            config.set("mapping", "map_night", 'true')
            config.set("mapping", "map_oblique", 'true')           
            config.set("mapping", "map_oblique_night", 'true')
            config.set("mapping", "map_oblique_cave", 'true')
            config.set("mapping", "map_hell", 'true')
            config.set("mapping", "map_hell_oblique", 'true')

            config.add_section("java")
            config.set("java", "java_path", self.mineos_config['template']['java_path'])
            config.set("java", "java_bin", self.mineos_config['template']['java_bin'])
            config.set("java", "java_tweaks", self.mineos_config['template']['java_tweaks'])

            if arguments.get('server_jar') == 'craftbukkit-0.0.1-SNAPSHOT.jar':
                config.set("java", "server_jar", self.mineos_config['downloads']['bukkit_jar'])
                config.set("java", "server_jar_args", self.mineos_config['template']['bukkit_args'])
            elif arguments.get('server_jar') == 'CanaryMod.jar':
                config.set("java", "server_jar", 'CanaryMod.jar')
                config.set("java", "server_jar_args", self.mineos_config['template']['canary_args'])
            elif arguments.get('server_jar') == 'minecraft_server.jar':
                config.set("java", "server_jar", self.mineos_config['downloads']['mc_jar'])
                config.set("java", "server_jar_args", self.mineos_config['template']['pure_args'])
            else:
                config.set("java", "server_jar", arguments.get('server_jar'))
                config.set("java", "server_jar_args", self.mineos_config['template']['pure_args'])                

            if status == 'foreign':
                sp = os.path.join(self.cwd, 'server.properties')
                config.set('minecraft', 'port', str(mc.attribute_find(sp, 'server-port', self.server_name)))
                config.set('minecraft', 'max_players', str(mc.attribute_find(sp, 'max-players', self.server_name)))

            logging.info('(%s) creating new server.config template', self.server_name)

            mc.config_save(os.path.join(self.cwd, 'server.config'), config)

            logging.info('(%s) server creation complete', self.server_name)
            print '(%s) server creation complete' % self.server_name

        elif status == 'up':
            logging.error('(%s) world exists and is running--no action taken', self.server_name)
            raise ServerRunningException(self.server_name, 'create')
        elif status == 'down':
            logging.error('(%s) world exists--no action taken', self.server_name)
            raise ServerExistsException(self.server_name, 'create')
        elif status == 'unclean':
            logging.error('(%s) world exists and lockfiles present--no action taken', self.server_name)
            raise ServerUncleanException(self.server_name, 'create')
        elif status == 'template':
            logging.error('(%s) server.config template already exists--no action taken', self.server_name)
            raise ServerTemplateException(self.server_name, 'create')     

    def start(self):
        def create_dummy_sp(filename, port, max_players, level_seed='', gamemode='0', difficulty='1', level_type='DEFAULT'):
            logging.info('(%s) <create_dummy_sp>', self.server_name)
            sp_file = open(os.path.join(filename), "w")
            lines = ["server-port=%s\n" % port,
                     "max-players=%s\n" % max_players,
                     "level-seed=%s\n" % level_seed,
                     "gamemode=%s\n" % gamemode,
                     "difficulty=%s\n" % difficulty,
                     "level-type=%s\n" % level_type]
            logging.info('(%s) writing to file: %s', self.server_name, filename)
            sp_file.writelines(lines)
            sp_file.close()
            
        logging.info('(%s) <start>', self.server_name)
        status = self.status()

        if status == 'foreign':
            logging.error('(%s) server not from MineOS, created server.config--please restart server', self.server_name)
            raise ServerForeignException(self.server_name)
            #self.create()
        if status == 'unclean':
            self.clean()
            status = self.status()

        sp = os.path.join(self.cwd, 'server.properties')
        sc = os.path.join(self.cwd, 'server.config')

        if status in ['down', 'template']:

            if self.server_config['java']['server_jar'] == 'CanaryMod.jar':
                self.update_canary()
            
            if status == 'template':
                logging.info('(%s) no server.properties exists, creating temp...', self.server_name)
                create_dummy_sp(sp,
                                self.server_config['minecraft']['port'],
                                self.server_config['minecraft']['max_players'],
                                self.server_config['minecraft']['level_seed'],
                                self.server_config['minecraft']['gamemode'],
                                self.server_config['minecraft']['difficulty'])
            
            sp_mtime = os.path.getmtime(sp)
            sc_mtime = os.path.getmtime(sc)
                
            port = int(mc.attribute_find(sp, 'server-port', self.server_name))
            if port != int(self.server_config['minecraft']['port']):
                logging.warning('(%s) server.config port set to %s', self.server_name, self.server_config['minecraft']['port'])
                logging.warning('(%s) server.properties port set to %s', self.server_name, port)
                if sp_mtime > sc_mtime:
                    logging.warning('(%s) setting server.config to %s', self.server_name, port)
                    mc.config_alter(sc, 'minecraft', 'port', port)
                else:
                    logging.warning('(%s) setting server.properties to %s', self.server_name, self.server_config['minecraft']['port'])
                    mc.attribute_change(sp, 'server-port', self.server_config['minecraft']['port'], self.server_name)
                    port = self.server_config['minecraft']['port']

            if port not in mc.ports_in_use().values():
                logging.info('(%s) starting server using port %s', self.server_name, self.server_config['minecraft']['port'])

                screen_config = ''
                os.chdir(self.cwd)
                logging.debug('(%s) changedir %s', self.server_name, self.cwd)

                if self.server_config['java']['server_jar'] == 'CanaryMod.jar':
                    server_jar_path = os.path.join(self.cwd, self.server_config['java']['server_jar'])

                    version_txt = os.path.join(self.cwd, 'version.txt')
                    if os.access(version_txt, os.F_OK):
                        os.remove(version_txt)
                        logging.debug('(%s) deleted %s', version_txt)
                    else:
                        logging.debug('(%s) did not delete %s', version_txt)
                else:
                    server_jar_path = os.path.join(self.mineos_config['paths']['mc_path'], self.server_config['java']['server_jar'])

                execute_command = "screen %s -dmS mc-%s %s %s %s -jar %s %s" % \
                                  (screen_config, 
                                   self.server_name, 
                                   os.path.join(self.server_config['java']['java_path'], self.server_config['java']['java_bin']),
                                   self.server_config['java']['java_tweaks'],
                                   '-Xmx%sM -Xms%sM' % (self.server_config['minecraft']['mem'], self.server_config['minecraft']['mem']),
                                   server_jar_path,
                                   self.server_config['java']['server_jar_args'])
                logging.debug('%s', execute_command)
                os.system(execute_command)
                for z in xrange(15):
                    time.sleep(2)
                    if self.status() == 'up':
                        break
                status = self.status()
                logging.info('(%s) status: %s', self.server_name, status)
                print '(%s) server started' % (self.server_name)
            else:
                logging.error('(%s) server already running on port: %s', self.server_name, int(self.server_config['minecraft']['port']))
                raise PortInUseException(self.server_name, port)
        elif status == 'up':
            logging.error('(%s) server already up--no action taken', self.server_name)
            raise ServerRunningException(self.server_name, 'start')
        elif status == 'unclean':
            logging.error('(%s) world locks present and could not remove--no action taken', self.server_name)
            raise ServerUncleanException(self.server_name, 'start')
        elif status == 'empty':
            logging.error('(%s) server directory exists but is empty--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'start')
        elif status == 'not-found':
            logging.error('(%s) server directory does not exist--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'start')

    def stop(self):
        logging.info('(%s) <stop>', self.server_name)
        status = self.status()
        
        if status == 'down':
            logging.error('(%s) server already down--no action taken', self.server_name)
        elif status == 'up':
            logging.info('(%s) attempting to stop server', self.server_name)
            execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "stop\012"\'' % self.server_name
            logging.debug('%s', execute_command)
            os.system(execute_command)
            for z in xrange(12):
                time.sleep(2)
                if self.status() == 'down':
                    break
            if self.status() in ['up', 'unclean']:
                logging.warning('(%s) after stop, 1+ lock files still exist: cleaning...', self.server_name)
                self.clean()
            logging.info('(%s) status: %s', self.server_name, self.status())
            print '(%s) server status: %s' % (self.server_name, self.status())
        elif status == 'unclean':
            logging.info('(%s) attempting to stop server', self.server_name)
            execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "stop\012"\'' % self.server_name
            logging.debug('%s', execute_command)
            os.system(execute_command)
            time.sleep(3)
            self.clean()
            print '(%s) server status: %s' % (self.server_name, self.status())
        elif status == 'empty':
            logging.error('(%s) server directory exists but is empty--no action taken', self.server_name)
            raise ServerDownException(self.server_name, 'stop')
        elif status == 'not-found':
            logging.error('(%s) server directory does not exist--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'stop')
            
    def clean(self):
        logging.info('(%s) <clean>', self.server_name)
        try:
            server_log_lck = os.path.join(self.cwd, 'server.log.lck')
            if os.access(server_log_lck, os.F_OK):
                os.remove(server_log_lck)
                logging.info('(%s) removed server.log.lck', self.server_name)
        except:
            logging.error('(%s) deletion of server.log.lck failed', self.server_name)

        try:
            session_lock = os.path.join(self.cwd,
                                        mc.attribute_find(os.path.join(self.cwd, 'server.properties'), 'level-name', self.server_name) or 'world',
                                        'session.lock')
            if os.access(session_lock, os.F_OK):
                os.remove(session_lock)
                logging.info('(%s) removed session.lock', self.server_name)
        except:
            logging.error('(%s) deletion of session.lock failed', self.server_name)

    def archive(self):
        logging.info('(%s) <archive>', self.server_name)
        archive_filename = 'server-' + self.server_name + '_' + time.strftime("%Y-%m-%d_%H:%M:%S") + '.tar.gz'

        try:
            if not os.path.exists(self.awd): os.makedirs(self.awd)
        except:
            logging.warning('(None) unable to create directory %s', path)

        status = self.status()
        if status == 'foreign':
            mc(self.server_name).create()
            status == self.status()
                    
        if status == 'up':
            self.commit()
            self.commit_off()
            execute_command = 'nice -n 10 tar czf %s .' % os.path.join(self.awd, archive_filename)
            logging.debug('%s', execute_command)
            os.chdir(self.cwd)
            output = subprocess.check_output(shlex.split(execute_command))
            #print str(output).replace('\n', mc.linebreak)
            self.commit_on()
            logging.info('(%s) archive complete: %s', self.server_name, archive_filename)
            print '(%s) archive complete: %s' % (self.server_name, archive_filename)
        elif status in ['down', 'unclean']:
            execute_command = 'nice -n 10 tar czf %s .' % os.path.join(self.awd, archive_filename)
            logging.debug('%s', execute_command)
            os.chdir(self.cwd)
            output = subprocess.check_output(shlex.split(execute_command))
            #print str(output).replace('\n', mc.linebreak)
            logging.info('(%s) archive complete: %s', self.server_name, archive_filename)
            print '(%s) archive complete: %s' % (self.server_name, archive_filename)
        else:
            logging.error('(%s) server does not exist--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'archive')

    def backup(self):
        logging.info('(%s) <backup>', self.server_name)
        status = self.status()

        try:
            if self.status_backup() == 'not-found': os.makedirs(self.bwd)
        except:
            logging.warning('(None) unable to create directory %s', path)

        if status == 'foreign':
            mc(self.server_name).create()
            status == self.status()

        if status == 'up':
            self.commit()
            self.commit_off()
            execute_command = 'nice -n 10 rdiff-backup %s/ %s' % (self.cwd, self.bwd)
            logging.debug('%s', execute_command)
            output = subprocess.check_output(shlex.split(execute_command))
            #print str(output).replace('\n', mc.linebreak)
            self.commit_on()
            logging.info('(%s) backup complete', self.server_name)
            print '(%s) backup complete.' % self.server_name
        elif status in ['down', 'unclean']:
            execute_command = 'nice -n 10 rdiff-backup %s/ %s' % (self.cwd, self.bwd)
            logging.debug('%s', execute_command)
            output = subprocess.check_output(shlex.split(execute_command))
            #print str(output).replace('\n', mc.linebreak)
            logging.info('(%s) backup complete', self.server_name)
            print '(%s) backup complete.' % self.server_name
        else:
            logging.error('(%s) server does not exist--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'backup')
            
    def commit(self):
        logging.info('(%s) <commit>', self.server_name)
        logging.info('(%s) committing live world chunks to disk...', self.server_name)
        execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "save-all\012"\'' % self.server_name
        logging.debug('%s', execute_command)
        os.system(execute_command)
        time.sleep(1)

    def commit_off(self):
        logging.info('(%s) <commit_off>', self.server_name)
        logging.info('(%s) disabling chunk commit...', self.server_name)
        execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "save-off\012"\'' % self.server_name
        logging.debug('%s', execute_command)
        os.system(execute_command)

    def commit_on(self):
        logging.info('(%s) <commit_on>', self.server_name)
        logging.info('(%s) enabling chunk commit...', self.server_name)
        execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "save-on\012"\'' % self.server_name
        logging.debug('%s', execute_command)
        os.system(execute_command)        

    def restore(self, steps='now', force=False):
        logging.info('(%s) <restore>', self.server_name)
        status = self.status()
        backup_status = self.status_backup()

        if force:
            if backup_status not in ['unclean', 'found']:
                logging.error('(%s) no backups found for server at: %s--no action taken', self.server_name, self.bwd)
                raise ServerNotFoundException(self.server_name, 'restore')
            elif status == 'up':
                logging.error('(%s) server is running, can not restore--no action taken', self.server_name)
                raise ServerRunningException(self.server_name, 'restore')
            elif backup_status in ['unclean', 'found']:
                if status in ['unclean', 'down', 'empty', 'not-found', 'foreign']:
                    if status == 'not-found': os.makedirs(self.cwd)
                    
                    logging.info('(%s) attempting force restore (backtrack): %s', self.server_name, steps)
                    execute_command = "rdiff-backup --force --restore-as-of %s --exclude '**rdiff-backup-data' %s %s" % \
                                      (steps, self.bwd, self.cwd)
                    logging.debug('%s', execute_command)
                    output = subprocess.check_output(shlex.split(execute_command))
                    logging.info('(%s) restored world status: %s', self.server_name, self.status())
                    print '(%s) restore complete' % self.server_name
                    if self.status() in ['unclean', 'up']: self.clean()
            else:
                raise FailedRestoreException(self.server_name, status, backup_status)
        else:
            if backup_status not in ['unclean', 'found']:
                logging.error('(%s) no backups found for server at: %s--no action taken', self.server_name, self.bwd)
                raise ServerNotFoundException(self.server_name, 'restore')
            elif status in ['up', 'unclean', 'down']:
                logging.error('(%s) server exists/is running, can not restore--no action taken', self.server_name)
                raise ServerRunningException(self.server_name, 'restore')
            elif backup_status in ['unclean', 'found'] and status in ['empty', 'not-found']:
                logging.info('(%s) attempting restore', self.server_name)
                execute_command = "rdiff-backup --restore-as-of %s --exclude '**rdiff-backup-data' %s %s" % \
                                      (steps, self.bwd, self.cwd)
                logging.debug('%s', execute_command)
                output = subprocess.check_output(shlex.split(execute_command))
                logging.info('(%s) restored world status: %s', self.server_name, self.status())
                print '(%s) restore complete' % self.server_name
                if self.status() in ['unclean', 'up']: self.clean()
            else:
                raise FailedRestoreException(self.server_name, status, backup_status)
            
    def prune(self, steps):
        logging.info('(%s) <prune>', self.server_name)
        status = self.status()
        backup_status = self.status_backup()

        if backup_status in ['unclean', 'found']:
            logging.info('(%s) attempting pruning of backups older than: %s', self.server_name, steps)
            execute_command = "rdiff-backup --force --remove-older-than %s %s" % \
                              (steps, self.bwd)
            logging.debug('%s', execute_command)
            output = subprocess.check_output(shlex.split(execute_command))
            #print str(output).replace('\n', mc.linebreak)
            logging.info('(%s) pruning complete', self.server_name)
            print '(%s) pruning complete' % self.server_name
        else:
            logging.error('(%s) server has no backups--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'prune')

    def importworld(self, filename):
        import shutil, tarfile, zipfile
        logging.info('(%s) <importworld>', self.server_name)
        status = self.status()
        execute_command = None

        if status in ['empty', 'not-found']:
            if status == 'not-found': os.makedirs(self.cwd)

            try:
                filepath = os.path.join(self.mineos_config['paths']['import_path'], filename)
                if tarfile.is_tarfile(filepath):
                    logging.info('(None) %s is a valid tarfile, opening...', filename)
                    with tarfile.open(filepath, mode='r:gz') as tarchive:
                        tarchive.extractall(self.cwd)
                        pluginpath = os.path.join(self.cwd, 'plugins')
                        if os.path.islink(pluginpath):
                            logging.info('(None) tarfile has broken plugins symlink, deleting...')
                            os.unlink(pluginpath)
                            os.makedirs(pluginpath)
                        logging.info('(None) %s extracted.' % filename)
                        tarchive.close()
                elif zipfile.is_zipfile(filepath):
                    logging.info('(None) %s is a valid zipfile, opening...', filename)
                    with zipfile.ZipFile(filepath, mode='r') as zipchive:
                        zipchive.extractall(self.cwd)
                        zipchive.close()
                    logging.info('(None) %s extracted.' % filename)
            except:
                raise ArchiveUnexpectedException(self.server_name, filename) 

            status = self.status()
            if status in ['unclean', 'up']:
                self.clean()
                status = self.status()
            if status == 'foreign':
                raise ServerForeignException('imported')
            if status == 'down':
                logging.info('(%s) imported world status: %s', self.server_name, self.status())
                print '(%s) import complete' % self.server_name
            elif status in ['unclean', 'up']:
                logging.error('(%s) imported world, but one or more lock files remain--status: "%s"', self.server_name, self.status())
                print '(%s) import complete' % self.server_name
            else:
                logging.error('(%s) imported file\'s structure unexpected', self.server_name)
                shutil.rmtree(self.cwd)
                raise ArchiveUnexpectedException(self.server_name, filename)

        elif status in ['down', 'up', 'unclean']:
            logging.error('(%s) destination server already exists--no action taken', self.server_name)
            raise ServerExistsException(self.server_name, 'import')
        else:
            logging.error('(%s) destination directory must be empty (template exists)--no action taken', self.server_name)
            raise GenericException(self.server_name, 'import')

    def mapworld(self):
        def get_immediate_subdirectories(dir):
            return [name for name in os.listdir(dir)
                    if os.path.isdir(os.path.join(dir, name))]

        logging.info('(%s) <mapworld>', self.server_name)
        status = self.status()

        try:
            if not os.path.exists(self.swd): os.makedirs(self.swd)
        except:
            logging.error('(None) unable to create directory %s', path)

        if status == 'foreign':
            mc(self.server_name).create()
            status == self.status()

        if status in ['down', 'unclean', 'up']:
            styles = []
            if self.server_config['mapping']['map_standard'] == 'true':
                styles.append(('standard',      '.png',               '-M 512 -s -m 1'))
            if self.server_config['mapping']['map_caves'] == 'true':
                styles.append(('caves',         '_caves.png',         '-M 512 -s -m 1 -c'))   
            if self.server_config['mapping']['map_night'] == 'true':
                styles.append(('night',         '_night.png',         '-M 512 -s -m 1 -n'))
            if self.server_config['mapping']['map_oblique'] == 'true':
                styles.append(('oblique',       '_oblique.png',       '-M 512 -s -m 1 -q'))
            if self.server_config['mapping']['map_oblique_night'] == 'true':
                styles.append(('oblique_night', '_oblique_night.png', '-M 512 -s -m 1 -q -n'))
            if self.server_config['mapping']['map_oblique_cave'] == 'true':
                styles.append(('oblique_cave',  '_oblique_cave.png',  '-M 512 -s -m 1 -q -c'))
            if self.server_config['mapping']['map_hell'] == 'true':
                styles.append(('standard_hell', '_standard_hell.png', '-M 512 -N --hell-mode -s -z -m 1'))
            if self.server_config['mapping']['map_hell_oblique'] == 'true':
                styles.append(('oblique_hell', '_oblique_hell.png', '-M 512 -N --hell-mode -s -q -m 1'))
                
            lines = []

            for each_world in get_immediate_subdirectories(self.cwd):
                if os.path.exists(os.path.join(self.cwd, each_world, 'level.dat')):
                    for desc, png, modifiers in styles:
                        lines.append('nice -n 15 %s -w %s -o %s %s' %
                                 (os.path.join(self.mc_path, 'c10t', 'c10t'), 
                                  os.path.join(self.cwd, each_world), 
                                  os.path.join(self.swd, each_world + '_' + time.strftime("%Y-%m-%d_%H:%M:%S") + png), 
                                  modifiers))

            if status == 'up':
                self.commit()
                self.commit_off()

            for execute_command in lines:
                try:
                    logging.info('(%s) %s', self.server_name, execute_command)  
                    output = subprocess.check_output(shlex.split(execute_command))
                    #print str(output).replace('\n', mc.linebreak)
                except:
                    logging.error('(%s) %s', self.server_name, 'error creating map render')   

            if status == 'up':
                self.commit_on()

            if lines:
                print '(%s) mapping complete: %s' % (self.server_name, ', '.join(maptype[0] for maptype in styles))
            else:
                raise NoWorldFilesException(self.server_name)
            
        elif status in ['not-found', 'empty']:
            logging.error('(%s) server does not exist--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'map')
        else:
            logging.error('(%s) server does not exist--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'map')

    def pigmap(self, full=None):
        import string, glob
        def pigmapper(inputpath, outputpath, diff=None):
            if diff:
                pigmap_args = ''
                nice = 'nice -x -n 15 %s -i %s -o %s -g %s -r %s %s' % ('./pigmap',
                                                                     inputpath,
                                                                     outputpath,
                                                                     os.path.join(mc.mc_path, 'pigmap'),
                                                                     os.path.join(mc.mc_path, diff),
                                                                     pigmap_args)
                return 'ionice -c3 %s -i %s -o %s -g %s -r %s %s' % ('./pigmap',
                                                                     inputpath,
                                                                     outputpath,
                                                                     os.path.join(mc.mc_path, 'pigmap'),
                                                                     os.path.join(mc.mc_path, diff),
                                                                     pigmap_args)
            else:
                pigmap_args = '-B 6 -T 1 -Z 10'
                return 'nice -n 15 %s -i %s -o %s -g %s %s' % ('./pigmap',
                                                               inputpath,
                                                               outputpath,
                                                               os.path.join(mc.mc_path, 'pigmap'),
                                                               pigmap_args)
        
        def md5sum(filepath):
            import hashlib
            
            infile = open(os.path.join(filepath), 'r')
            content = infile.read()
            infile.close()
            m = hashlib.md5()
            m.update(content)
            md5 = m.hexdigest()
            return md5

        logging.info('(%s) <pigmap>', self.server_name)

        for relpath in self.find_regiondirs():
            worldname = relpath.split('/')[0]

            if string.find(worldname, '_nether') >= 0:
                adjustedpath = os.path.join(worldname, 'DIM-1')
            elif string.find(relpath, 'DIM-1') >= 0:
                adjustedpath = os.path.join(worldname, 'DIM-1')
                worldname = '%s_nether' % worldname
            else:
                adjustedpath = worldname

            if os.access(os.path.join(self.mwd, adjustedpath, 'pigmap.params'), os.R_OK) and \
               not full:
                md5dict = {}
                try:
                    with open(self.cwd + '/%s.md5' % worldname, 'r') as md5list:
                        for line in md5list:
                            split = line.strip('\n').split(' ')
                            md5dict[split[0]] = split[1]
                        md5list.close()
                except IOError:
                    logging.error('(%s) pigmap destdir found but no .md5 file', self.server_name)

                with open(self.cwd + '/%s.diff' % worldname, 'w') as md5file:
                    for mcr in glob.glob(os.path.join(self.cwd, relpath) + '/*.mcr'):
                        if mcr in md5dict:
                            if md5dict[mcr] != md5sum(mcr):
                                md5file.write('%s\n' % mcr)
                                logging.info('(%s) %s : added to pigmap queue', self.server_name, mcr)
                            else:
                                logging.info('(%s) %s : skipped in pigmap queue', self.server_name, mcr)
                        else:
                            md5file.write('%s\n' % mcr)
                            logging.info('(%s) %s : added to pigmap queue', self.server_name, mcr)   
                    md5file.close()

                execute_command = pigmapper(os.path.join(self.cwd, adjustedpath),
                                            os.path.join(self.mwd, adjustedpath),
                                            os.path.join(self.cwd, '%s.diff' % worldname))
                logging.info('(%s) %s', self.server_name, execute_command)
                os.chdir(os.path.join(self.mc_path, 'pigmap'))
                os.system(execute_command)       
            else:                    
                execute_command = pigmapper(os.path.join(self.cwd, adjustedpath),
                                            os.path.join(self.mwd, adjustedpath),
                                            None)
                logging.info('(%s) %s', self.server_name, execute_command)
                os.chdir(os.path.join(self.mc_path, 'pigmap'))
                os.system(execute_command)

            with open(self.cwd + '/%s.md5' % worldname, 'w') as md5file:
                for mcr in glob.iglob(os.path.join(self.cwd, relpath) + '/*.mca'):
                    md5file.write('%s %s\n' % (mcr, md5sum(mcr)))
                md5file.close()

    def find_regiondirs(self):
        import glob

        os.chdir(os.path.join(self.cwd))
        paths = []
        paths.extend(glob.glob('*/region'))
        paths.extend(glob.glob('*/*/region'))
        return paths

    def say(self, message):
        logging.info('(%s) <say>', self.server_name)
        status = self.status()

        if status == 'up':
            logging.info('(%s) say: %s', self.server_name, message)
            execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "say %s\012"\'' % (self.server_name, message)
            logging.debug('%s', execute_command)
            os.system(execute_command)
            print '(%s) say: %s' % (self.server_name, message)
        elif status in ['not-found', 'empty']:
            logging.error('(%s) server does not exist--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'map')
        else:
            logging.error('(%s) server not up--no action taken', self.server_name)
            raise ServerDownException(self.server_name, 'say')

    def command(self, command):
        logging.info('(%s) <command>', self.server_name)
        status = self.status()

        if status == 'up':
            logging.info('(%s) %s:', self.server_name, command)
            execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "%s\012"\'' % (self.server_name, command)
            logging.debug('%s', execute_command)
            os.system(execute_command)
            print '(%s) command: %s' % (self.server_name, command)
        elif status in ['not-found', 'empty']:
            logging.error('(%s) server does not exist--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'command')
        else:
            logging.error('(%s) server not up--no action taken', self.server_name)
            raise ServerDownException(self.server_name, 'command')

    def list_backups(self):
        logging.info('(%s) <list_backups>', self.server_name)
        status = self.status()
        backup_status = self.status_backup()

        if backup_status in ['unclean', 'found']:
            logging.info('(%s) displaying increments', self.server_name)
            execute_command = "rdiff-backup -l %s" % self.bwd
            logging.debug('(%s) %s', self.server_name, execute_command)
            output = subprocess.check_output(shlex.split(execute_command))
            return output.split('\n')
        else:
             logging.error('(%s) server has no backups--no action taken', self.server_name)
             return []

    def list_players(self):
        import re
        status = self.status()

        if status == 'up':
            logging.info('(%s) <list>', self.server_name)
            execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "list\012"\'' % (self.server_name)
            logging.debug('(%s) %s', self.server_name, execute_command)
            os.system(execute_command)
            
            execute_command = "tac %s | grep -m 1 'Connected players:'" % os.path.join(self.cwd, 'server.log')
            execute_command_tac = "tac %s" % os.path.join(self.cwd, 'server.log')
            execute_command_grep = "grep -m 1 'Connected players:'"
            p1 = subprocess.Popen(shlex.split(execute_command_tac), stdout=subprocess.PIPE)
            p2 = subprocess.Popen(shlex.split(execute_command_grep), stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()
            output = p2.communicate()[0]
            
            p = re.compile('[^I]+INFO] Connected players:(.*)', re.IGNORECASE)
            match = None

            try:
                match = p.match(output).group(1)
                match = match.strip().replace(',', '').split(' ')
                match.remove('0]m')
            except ValueError:
                pass
            except AttributeError:
                return []
            
            return filter(bool, match) or []
        else:
            logging.error('(%s) server is not up--no active players', self.server_name)
            return []

    def rename(self, newname):
        logging.info('(%s) renaming server', self.server_name)
        status = self.status()

        newdir = os.path.join(self.mineos_config['paths']['world_path'], newname)
        
        if status in ['down', 'unclean']:
            try:
                os.rename(self.cwd, newdir)
                if os.path.exists(self.bwd):
                    os.rename(self.bwd, os.path.join(self.mineos_config['paths']['backup_path'], newname))
                else:
                    os.makedirs(os.path.join(self.mineos_config['paths']['backup_path'], newname))
                if os.path.exists(self.awd):
                    os.rename(self.awd, os.path.join(self.mineos_config['paths']['archive_path'], newname))
                else:
                    os.makedirs(os.path.join(self.mineos_config['paths']['archive_path'], newname))
                if os.path.exists(self.swd):
                    os.rename(self.swd, os.path.join(self.mineos_config['paths']['snapshot_path'], newname))
                else:
                    os.makedirs(os.path.join(self.mineos_config['paths']['snapshot_path'], newname))
                if os.path.exists(self.mwd):
                    os.rename(self.mwd, os.path.join(self.mineos_config['paths']['http_snapshot_path'], newname))
                else:
                    os.makedirs(os.path.join(self.mineos_config['paths']['http_snapshot_path'], newname))

                logging.info('(%s) server renamed to %s', self.server_name, newname)
                print '(%s) server renamed to %s' % (self.server_name, newname)
            except:
                logging.error('(%s) server %s already exists--no action taken', self.server_name, newname)
                os.rename(newdir, self.cwd)
                os.rename(os.path.join(self.mineos_config['paths']['backup_path'], newname), self.bwd)
                os.rename(os.path.join(self.mineos_config['paths']['archive_path'], newname), self.awd)
                os.rename(os.path.join(self.mineos_config['paths']['snapshot_path'], newname), self.swd)
                os.rename(os.path.join(self.mineos_config['paths']['http_snapshot_path'], newname), self.mwd)
                raise RenameFailedException(self.server_name, newname)
        elif status == 'up':
            logging.error('(%s) server is currently running, cannot rename--no action taken', self.server_name)
            raise ServerRunningException(self.server_name, 'rename')
        else:
            logging.error('(%s) server is not suitable for renaming--no action taken', self.server_name)
            raise ServerNotFoundException(self.server_name, 'rename')

    def log_dump(self):        
        import fileinput
        logging.info('(%s) dumping logs to console', self.server_name)
        filepath = os.path.join(self.cwd, 'server.log')
        execute_command = 'tail -n 200 %s' % filepath
        output = subprocess.check_output(shlex.split(execute_command))
        print str(output)

    def log_archive(self):
        import gzip
        logging.info('(%s) gzipping server logs', self.server_name)
        filepath = os.path.join(self.cwd, 'server.log')

        if self.status() in ['down', 'unclean']:
            f_in = open(filepath, 'rb')
            f_out = gzip.open(filepath + '-' + time.strftime("%Y-%m-%d_%H:%M:%S") + '.gz', 'wb')
            f_out.writelines(f_in)
            f_out.close()
            f_in.close()
            with open(filepath, 'w') as f_in:
                f_in.close()
            print '(%s) existing logs gzipped and server.log emptied' % self.server_name
        else:
            raise ServerRunningException(self.server_name, 'gzipping server.log')

    @staticmethod
    def list_build_date(filepath):
        import zipfile, time

        if zipfile.is_zipfile(filepath):
            with zipfile.ZipFile(filepath, mode='r') as zipchive:
                info = zipchive.getinfo("META-INF/MANIFEST.MF")
                zipchive.close()
                return "%s/%s/%s" % (str(info.date_time[1]).rjust(2,'0'), str(info.date_time[2]).rjust(2,'0'), str(info.date_time[0]).rjust(2,'0') )
        else:
            return time.strftime("%m/%d/%Y", time.localtime(os.path.getmtime(filepath)))  

    @staticmethod
    def list_imports():
        import tarfile, zipfile
        importable = []
        
        for files in os.listdir(mc().mineos_config['paths']['import_path']):
            filepath = os.path.join(mc().mineos_config['paths']['import_path'], files)
            if tarfile.is_tarfile(filepath) or zipfile.is_zipfile(filepath):
                importable.append(files)
        return importable

    @staticmethod
    def list_server_frequency(action, frequency):
        docket = []
        for server, port, status in mc.ports_reserved():
            if frequency == mc(server).server_config['crontabs']['freq_' + action]:
                docket.append(server)
        return docket

    @staticmethod
    def list_server_reboot(action):
        docket = []

        if action == 'start':
            for server, port, status in mc.ports_reserved():
                if mc(server).server_config['onreboot']['start'] == 'true':
                    docket.append(server)
        elif action == 'restore':
            for server, port, status in mc.ports_reserved_backup():
                sc = os.path.join(mc().mineos_config['paths']['backup_path'], server, 'server.config')
                config = mc.config_import(sc)
                try:
                    if config['onreboot']['restore'] == 'true':
                        docket.append(server)
                except KeyError:
                    raise NoOnRebootSectionException(server, sc)
        return docket

    @staticmethod
    def ports_reserved():
        reservations = []

        for hit in os.listdir(mc().mineos_config['paths']['world_path']):
            server = mc(hit)
            status = server.status()
            if status in ['up', 'down', 'unclean', 'template']:
                reservations.append((hit, server.server_config['minecraft']['port'], status))
            if status in ['foreign']:
                port = mc.attribute_find(os.path.join(server.cwd, 'server.properties'), 'server-port', server.server_name)
                reservations.append((hit, port, status))
        return reservations

    @staticmethod
    def ports_reserved_backup():
        reservations = []

        for hit in os.listdir(mc().mineos_config['paths']['backup_path']):
            server = mc(hit)
            status = server.status_backup()
            if status in ['found', 'unclean']:
                port = mc.attribute_find(os.path.join(server.bwd, 'server.properties'), 'server-port', server.server_name)
                reservations.append((hit, port, status))
        return reservations

    @staticmethod
    def ports_in_use():
        pairs = {}

        for hit in os.listdir(mc().mineos_config['paths']['world_path']):
            server = mc(hit)
            if server.status() == 'up':
                pairs[hit] = int(server.server_config['minecraft']['port'])
        return pairs

    @staticmethod
    def config_import(filename):
        class conf_parser(ConfigParser.ConfigParser):
            def as_dict(self):
                d = dict(self._sections)
                for k in d:
                    d[k] = dict(self._defaults, **d[k])
                    d[k].pop('__name__', None)
                return d
            
        config = conf_parser(allow_no_value=True)
        if config.read(filename):
            return config.as_dict()

    @staticmethod
    def config_section_add(filename, section):
        logging.info('(None) <config_section_add>')
        config = ConfigParser.SafeConfigParser(allow_no_value=True)
        config.read(filename)
        config.add_section("onreboot")
        mc.config_save(filename, config)

    @staticmethod
    def config_save(filename, config):
        logging.info('(None) <config_save>')
        with open(filename, 'wb') as configfile:
            config.write(configfile)
        configfile.close()

    @staticmethod
    def config_alter(filename, section, key, value, server_name=None):
        logging.info('(None) <config_alter>')
        config = ConfigParser.SafeConfigParser(allow_no_value=True)
        logging.info('(None) reading %s', filename)
        config.read(filename)
        logging.info('(None) modifying %s/%s', key, value)
        config.set(section, key, str(value))
        logging.info('(None) commiting config changes')
        mc.config_save(filename, config)

    @staticmethod
    def config_add(filename, section, key, value, server_name=None):
        logging.info('(None) <config_add>')
        config = ConfigParser.SafeConfigParser(allow_no_value=True)
        logging.info('(None) reading %s', filename)
        config.read(filename)
        logging.info('(None) adding %s/%s', key, value)
        config.set(section, key, str(value))
        logging.info('(None) commiting config changes')
        mc.config_save(filename, config)

    @staticmethod
    def attribute_change(filename, key, value, server_name=None):
        import re, fileinput
        logging.info('(%s) <attribute_change>', server_name)
        try:
            p = re.compile('^'+key+'=(.+)', re.IGNORECASE)
            logging.info('(%s) reading %s', server_name, filename)
            inputfile = fileinput.FileInput(filename, inplace=1)
            for line in inputfile:
                if p.match(line):
                    logging.info('(%s) matched %s, filling in %s', server_name, key, value)
                    print "%s=%s" % (key, value)
                else:
                    print line,
        except:
            pass
        finally:
            inputfile.close()

    @staticmethod
    def attribute_find(filename, key, server_name=None):
        import re, fileinput
        logging.info('(%s) <attribute_find>', server_name)
        try:
            p = re.compile('^'+key+'=(.+)', re.IGNORECASE)
            inputfile = fileinput.FileInput(filename, mode='r')
            for line in inputfile:
                m = p.match(line)
                if m: x = m.groups()
        except:
            pass
        finally:
            inputfile.close()

        if 'x' in locals():
            logging.info('(%s) match found: %s=%s', server_name, key, x[0])
            return x[0]
        logging.warning('(%s) no match found: %s', server_name, key)
        return None

    @staticmethod
    def attribute_list(filename):
        import re
        pairs = []
        logging.info('(None) <attribute_list>')
        try:
            p = re.compile('(.+)=(.*)', re.IGNORECASE)
            for line in open(filename, 'r'):
                m = p.match(line)
                if m:
                    pairs.append(m.groups())
        except:
            pass
        return pairs

    @staticmethod
    def stopall():
        logging.info('(None) <stopall>')
        for hit, port, status in mc.ports_reserved():
            server = mc(hit)
            logging.info('(%s) attempting to stop server', hit)
            execute_command = 'screen -S mc-%s -p 0 -X eval \'stuff "stop\012"\'' % hit
            logging.debug('%s', execute_command)
            os.system(execute_command)
            time.sleep(1)
            server.clean()
        logging.info('(None) stopall cycle complete')
    
    @staticmethod
    def forcestop():
        logging.info('(None) <forcestop>')
        if mc.ports_in_use():
            logging.info('(None) attempting killall java')
            execute_command = 'killall java'
            logging.debug('%s', execute_command)
            try:
                output = subprocess.check_output(shlex.split(execute_command))
            except:
                logging.warning('(None) killall returned non-zero exit status (all instances may already be killed)')

        time.sleep(2)
        servers = mc.ports_reserved()
        for server_name, port, status in servers:
            if status in ['unclean', 'up']:
                mc(server_name).clean()
        
        logging.info('(None) all minecraft servers stopped')
        print '(None) all minecraft servers stopped'

    @staticmethod
    def list_server_jars():
        for jar in os.listdir(mc().mineos_config['paths']['mc_path']):
            if jar.lower().endswith('.jar') and \
               jar not in ['jarjar.jar', 'mysql-connector-java-bin.jar', 'Chunkster.jar']:
                yield jar

        if os.access(os.path.join(mc().mineos_config['paths']['mc_path'], 'canary', 'CanaryMod.jar'), os.F_OK):
            yield 'CanaryMod.jar'
                
class ConfigNotFoundException(Exception):
    '''mineos.config not found in pythons cwd'''
    def __init__(self, cwd):
        Exception.__init__(self)
        print '(MineOS) mineos.config was not found in the current working directory: %s' % cwd

class DownloadFailedException(Exception):
    '''urllib failed to download a file'''
    def __init__(self, filename, url):
        Exception.__init__(self)
        print '(MineOS) there was an error attempting to download %s from %s' % (filename, url)

class ServerRunningException(Exception):
    '''server is running therefore action cannot occur'''
    def __init__(self, server_name, action):
        Exception.__init__(self)
        print "(%s) '%s' not possible while server is running." % (server_name, action)

class ServerDownException(Exception):
    '''server is down therefore action cannot occur'''
    def __init__(self, server_name, action):
        Exception.__init__(self)
        print "(%s) '%s' not possible while server is down." % (server_name, action)

class ServerExistsException(Exception):
    '''server exists therefore action cannot occur'''
    def __init__(self, server_name, action):
        Exception.__init__(self)
        print "(%s) '%s' not possible if server currently exists." % (server_name, action)

class ServerUncleanException(Exception):
    '''server exists therefore action cannot occur'''
    def __init__(self, server_name, action):
        Exception.__init__(self)
        print "(%s) '%s' not possible if world lock currently exist." % (server_name, action)

class ServerTemplateException(Exception):
    '''server exists in template form only'''
    def __init__(self, server_name, action):
        Exception.__init__(self)
        print "(%s) '%s' not possible while server exists as template only." % (server_name, action)

class ServerForeignException(Exception):
    '''server has been placed in world_path not through import (lacks server.config)'''
    def __init__(self, server_name):
        Exception.__init__(self)
        print "(%s) server missing server.config--populating file with defaults..." % server_name
        mc(server_name).create()

class ServerNotFoundException(Exception):
    '''a server does not exist'''
    def __init__(self, server_name):
        Exception.__init__(self)
        print "(%s) server not found" % server_name

class PortInUseException(Exception):
    '''port already in use, therefore start failed'''
    def __init__(self, server_name, port):
        Exception.__init__(self)
        print "(%s) server already running on %s--start failed" % (server_name, port)

class ArchiveExtensionInvalidException(Exception):
    '''attempted import is not of valid extension'''
    def __init__(self, server_name, filename):
        Exception.__init__(self)
        print "(%s) imported file %s does not have a supported extension" % (server_name, filename)

class ArchiveUnexpectedException(Exception):
    '''supplied archive argument did not extract or ending format invalid'''
    def __init__(self, server_name, filename):
        Exception.__init__(self)
        print "(%s) archive (%s) did not extract or file structure unexpected" % (server_name, filename)

class GenericException(Exception):
    '''generic exception for failed action'''
    def __init__(self, server_name, action):
        Exception.__init__(self)
        print "(%s) '%s' errored out" % (server_name, action)

class RenameFailedException(Exception):
    '''rename failed'''
    def __init__(self, server_name, newname):
        Exception.__init__(self)
        print "(%s) rename to %s failed, undoing any directory renames" % (server_name, newname)

class NoWorldFilesException(Exception):
    '''no level.dat file found'''
    def __init__(self, server_name):
        Exception.__init__(self)
        print "(%s) no level.dat file located in server directory; no maps generated" % (server_name)

class NoBackupRegionsException(Exception):
    '''no region directories found for pigmap'''
    def __init__(self, server_name, path):
        Exception.__init__(self)
        print "(%s) region directory %s does not exist; make a backup before incremental mapping." % (server_name, path)
   
class InvalidServerNameError(Exception):
    '''rename failed'''
    def __init__(self):
        Exception.__init__(self)
        print "(None) A server cannot be created without a designation"

class FailedRestoreException(Exception):
    '''restore failed'''
    def __init__(self, server_name, status, backup_status):
        Exception.__init__(self)
        print "(%s) Restore failed with statuses: live (%s) | backup (%s)" % (server_name, status, backup_status)

class NoOnRebootSectionException(Exception):
    '''[onreboot] does not exist in server.config'''
    def __init__(self, server_name, sc):
        Exception.__init__(self)
        #print "(%s) [onreboot] section does not exist--adding to server.config" % (server_name)
        mc.config_section_add(sc, 'onreboot')
        mc.config_alter(sc, "onreboot", "restore", 'false', server_name)
        mc.config_alter(sc, "onreboot", "start", 'false', server_name)


