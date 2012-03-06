#!/usr/bin/python
"""A python script web-management interface to manage minecraft servers
   Designed for use with MineOS: http://minecraft.codeemo.com
"""

__author__ = "William Dizon"
__license__ = "GNU GPL v3.0"
__version__ = "0.4.11a"
__email__ = "wdchromium@gmail.com"

print "Content-Type: text/html"
print

import sys, cgi, cgitb, os
import mineos

cgitb.enable()

def cgi_to_dict(fieldStorage):
    params = {}
    for key in fieldStorage.keys():
        params[key] = fieldStorage[key].value
    return params

def display_about():
    print '''
    <p>MineOS is a Linux distribution designed for the sole purpose of hosting Minecraft worlds.
    It comes complete with web-admin interface, SSH interaction, and SCP capability for easy filesystem access.<p>

    <p>MineOS is created and maintained by
    William Dizon - <a href="mailto:wdchromium@gmail.com">wdchromium@gmail.com</a></p>
    
    <p>First edition of MineOS CRUX made public on July 28, 2011.</p>
    
    <p>MineOS home page: <a href="http://minecraft.codeemo.com/">http://minecraft.codeemo.com/</a></p>
    <p>This Linux distribution is designed from CRUX Linux 2.7. <br>
    MineOS CRUX / MineOS2 licensed as GNU GPL v3.0;<br>
    please cite accordingly and contact me if you have any questions or concerns on usage/derivatives.</p>

    <p>A copy of the GNU GPL can be found on the disc/install: <br>
    /root/LICENSE or online at <br>
    <a href="http://www.gnu.org/licenses/gpl-3.0.txt">http://www.gnu.org/licenses/gpl-3.0.txt</a></p>

    <p>Minecraft is copyright 2009-2011 Mojang AB.</p>

    <p>As per Markus Persson's request from Minecraft's website,
    this Linux distro does not contain ANY Minecraft files.
    The scripts are, however, designed to download/update
    files directly from the source: <a href="http://minecraft.net">http://minecraft.net</a></p>

    <p>These terms can be seen at: <a href="http://minecraft.net/copyright.jsp">http://minecraft.net/copyright.jsp</a></p>
    '''

def display_crontabs():
    print '''
    <script type="text/javascript">
    $('.sc').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "display",
                                      server: $(this).attr("id"),
                                      page: 'server.config' },
         function(data){ $('#main').html(data); });
    }));
    </script>
    '''
    print '<h2>System Crontabs</h2>'
    print '<p><span class="green">%s</span> servers were located in <span class="green">%s</a>:</p>' % (len(mineos.mc.ports_reserved()),
                                                     mineos.mc().mineos_config['paths']['world_path'])
    print '<pre><b>%s%s%s%s</b><br>' % ('{:<20}'.format('server'),
                                      '{:<14}'.format('archive'),
                                      '{:<14}'.format('backup'),
                                      '{:<14}'.format('map'))

    for server, port, status in mineos.mc.ports_reserved():
        instance = mineos.mc(server)
        print '<a href="#" class="sc stats" id="%s">%s</a>%s%s%s' % (server,
                                                               '{:<20}'.format(server),
                                                               '{:<14}'.format(instance.server_config['crontabs']['freq_archive']),
                                                               '{:<14}'.format(instance.server_config['crontabs']['freq_backup']),
                                                               '{:<14}'.format(instance.server_config['crontabs']['freq_map']))

def display_initial():
    print '''
    <script type="text/javascript">
        $('.updatemc').one("click", (function(event){
        event.preventDefault();
        $('.updatemc').html("downloading...");
        $('.updatemc').addClass("plaintext");
        $.post("cgi-bin/server.py", { command: "act", 
                                      action: "updatemc",
                                      server: "none"},
        function(data){  $('#main').html(data); });
    }));

    $('.createnew').click(function(event){
        $.get("cgi-bin/server.py", { command: "display", page: "createnew" },
            function(data){  $('#main').html(data); }
        );
    });
    </script>
    <p>Welcome to the MineOS admin panel!</p>
    <p>Using this web admin interface, you can handle all actions of your MineOS server:</p>
    <ul>
      <li>create new servers</li>
      <li>change memory allocated to each java instance, as well as edit server.properties</li>
      <li>backup, restore, map, archive your servers</li>
      <li>view the server logs</li>
      <li>import worlds from existing archives</li>
      <li>set scheduled tasks for backups and mapping</li>
    </ul>
    '''

    print '<h2>Server Checklist</h2>'
    print '<h3>Minecraft server files check:</h3>'
    print '<pre>'
    for filename in [mineos.mc().mineos_config['downloads']['mc_jar'],
                     mineos.mc().mineos_config['downloads']['bukkit_jar'],
                     mineos.mc().mineos_config['downloads']['tekkit_zip'],
                     mineos.mc().mineos_config['downloads']['canary_zip'],
                     mineos.mc().mineos_config['downloads']['c10t_tgz']]:
        filepath = os.path.join(mineos.mc().mineos_config['paths']['mc_path'], filename)
        if os.access(filepath, os.F_OK):
            if os.access(filepath, os.R_OK):
                print '{:<50}'.format('%s found and readable:' % filename), '<span class="green smallcaps">OK</span>' 
            else:
                print '{:<50}'.format('%s found but not readable:' % filename), '<span class="red smallcaps">CHECK PERMISSIONS</span>'
        else:
            print '{:<50}'.format('%s not found:' % filename), '<a href="#" class="updatemc">DOWNLOAD</a>'
    print '</pre>'

    print '<h3>Server List</h3>'
    print '<pre>'
    print '<a href="#" class="createnew green">Create a server</a>'

    server_list = mineos.mc.ports_reserved()
    try:
        for server in [server[0] for server in server_list]:
            print server
    except:
        print 'No servers set up!'
    
    print '</pre>'
            
def display_status():
    print '''
    <script type="text/javascript">
    $('.status').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "act",
                                      server: $(this).attr("id"),
                                      action: $(this).html() },
         function(data){ $('#main').html(data); });
         $(this).html("Executing command...");
         $(this).addClass("plaintext");
    }));
    
    $('.stats').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "display",
                                      server: $(this).attr("id"),
                                      page: 'stats' },
         function(data){ $('#main').html(data); });
    }));
    </script>'''

    print '<h2>%s</h2>' % 'All Servers'
    print '<p><span class="green">%s</span> servers were located in <span class="green">%s</a>:</p>' % (len(mineos.mc.ports_reserved()),
                                                     mineos.mc().mineos_config['paths']['world_path'])
    print '<pre><b>%s%s%s%s</b><br>' % ('{:<20}'.format('server'),
                                      '{:<12}'.format('port'),
                                      '{:<12}'.format('status'),
                                      '{:<8}'.format('online'))

    colors = {
        'template': '<span class="black">%s</span>' % '{:<12}'.format('template'),
        'down': '<span class="red">%s</span>' % '{:<12}'.format('down'),
        'up': '<span class="green">%s</span>' % '{:<12}'.format('up'),
        'unclean': '<span class="red">%s</span>' % '{:<12}'.format('unclean'),
        'foreign': '<span class="purple">%s</span>' % '{:<12}'.format('foreign'),
        }
    
    for server, port, status in mineos.mc.ports_reserved():
        print '<a href="#" class="stats" id="%s">%s</a>%s%s' % (server,
                                                                '{:<20}'.format(server),
                                                                '{:<12}'.format(port),
                                                                colors.get(status)),

        instance = mineos.mc(server)        
        print '{:<8}'.format('%s/%s' % (len(instance.list_players()),
                                        instance.server_config['minecraft']['max_players'])),

        print {
            'template': '<a href="#" class="status %s" id="%s">%s</a>' % (status, server, 'start'),
            'up': '<a href="#" class="status %s" id="%s">%s</a>' % (status, server, 'stop'),
            'down': '<a href="#" class="status %s" id="%s">%s</a>' % (status, server, 'start'),
            'unclean': '<a href="#" class="status %s" id="%s">%s</a>' % (status, server, 'clean'),
            'foreign': '<a href="#" class="status %s" id="%s">%s</a>' % (status, server, 'create'),
            }.get(status),

        print '<span id="activity_%s"></span>' % server
    print '</pre>'    

def display_logdump():
    print '''
    <script type="text/javascript">

        $('#commandtext').keypress(function(e){
            if(e.which == 13){
                e.preventDefault();
                $.post("cgi-bin/server.py", { command: "act",
                                              action: "consolecommand",
                                              server: $('#switch').val(),
                                              argument: $('#commandtext').val() },
                                              function(data){ $('#response').html(data);
                                                            $.post("cgi-bin/server.py", { command: "act",
                                                                                          action: "logdump",
                                                                                          server: $('#switch').val() },
                                                             function(data){ $('#logdumptext').html(data); });
                                                            });
            }
        });
    
        $('.display').click(function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "act",
                                      action: "logdump",
                                      server: $('#switch').val() },
         function(data){ $('#logdumptext').html(data); });
    });
        $('#sendcommand').click(function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "act",
                                      action: "consolecommand",
                                      server: $('#switch').val(),
                                      argument: $('#commandtext').val() },
                                      function(data){ $('#response').html(data);
                                                    $.post("cgi-bin/server.py", { command: "act",
                                                                                  action: "logdump",
                                                                                  server: $('#switch').val() },
                                                     function(data){ $('#logdumptext').html(data); });
                                                    });
    });
    </script>'''
    print '<h2>Console and Server Logs</h2>'
    print '<a href="#" class="display actionbutton">Display</a>'
    print '<select id="switch" name="server">'
    for server, port, status in mineos.mc.ports_reserved():
        if status in ['up', 'down', 'foreign', 'unclean']:
            print '<option>%s</option>' % server
    print '</select>'
    print '<textarea id="logdumptext" cols="60" rows="20" readonly="readonly"></textarea><br>'
    print '''
    <form id="commandform">
        <input name="command" type="hidden" value="act">
        <input name="action" type="hidden" value="command">
        <table>
            <tr> 
                <td colspan="2"><label for="command">command:</label></td>
                <td colspan="2"><input type="text" id="commandtext" size="45" value="" /></td>
            </tr>
            <tr> 
                <td colspan="2"><a href="#" id="sendcommand" class="actionbutton">Send Command</a></td>
                <td colspan="2"><span id="response"></span></td>
            </tr>
        </table>
    </form>'''

def display_mineoslogdump():
    print '''
    <script type="text/javascript">    
        $.post("cgi-bin/server.py", { command: "act",
                                      action: "mineoslogdump",
                                      server: "none" },
         function(data){ $('#logdumptext').html(data); });
    </script>'''
    print '<h2>MineOS Logs</h2>'
    print '<textarea id="logdumptext" cols="60" rows="20" readonly="readonly"></textarea><br>'

def display_bam(page):
    print '''
    <script type="text/javascript">
        $('.%s').one("click", (function(event){
        event.preventDefault();
        $(this).addClass("plaintext");
        $.post("cgi-bin/server.py", { command: "act", 
                                      server: $(this).attr("id"), 
                                      action: $(this).html() },
         function(data){ $('#main').html(data); });
         $(this).html("Executing command...");
    }));

        $('.archive_logs').one("click", (function(event){
        event.preventDefault();
        $(this).addClass("plaintext");
        $.post("cgi-bin/server.py", { command: "act", 
                                      server: $(this).attr("id"), 
                                      action: 'log_archive' },
         function(data){ $('#main').html(data); });
         $(this).html("Executing command...");
    }));
    </script>''' % page
    print '<h2>%s</h2>' % page.title()

    print '<p><span class="green">%s</span> servers were located in <span class="green">%s</a>:</p>' % (len(mineos.mc.ports_reserved()),
                                                                                                        mineos.mc().mineos_config['paths']['world_path'])
    print '<pre><b>%s%s%s</b><br>' % ('{:<20}'.format('server'),
                               '{:<12}'.format('freq'),
                               '{:<12}'.format('status'))

    colors = {
        'template': '<span class="black">%s</span>' % '{:<12}'.format('template'),
        'down': '<span class="red">%s</span>' % '{:<12}'.format('down'),
        'up': '<span class="green">%s</span>' % '{:<12}'.format('up'),
        'unclean': '<span class="red">%s</span>' % '{:<12}'.format('unclean'),
        'foreign': '<span class="purple">%s</span>' % '{:<12}'.format('foreign'),
        }
    
    for server, port, status in mineos.mc.ports_reserved():
        print '%s%s%s' % ('{:<20}'.format(server),
                          '{:<12}'.format(mineos.mc(server).server_config['crontabs']['freq_%s' % page]),
                          colors.get(status)),

        if status in ['up', 'down', 'unclean']:
            print '<a href="#" class="%s" id="%s">%s</a>' % (page, server, page),
        else:
            print '%s'% page,

        if status == 'down' and page == 'archive':
            print '<a href="#" class="%s" id="%s">%s</a>' % ('archive_logs', server, 'gzip server.log'),
        print

    print '</pre>'

def display_rename(server_name):
    print '''
    <script type="text/javascript">
        $('#renamebutton').one("click", (function(event){
            event.preventDefault();
            $.post("cgi-bin/server.py", $('#renameform').serialize(),
            function(data){ $('#main').html(data); });
        }));
    </script>'''
    print '<h2>Renaming server %s</h2>' % server_name
    print '''
    <form id="renameform" class="renameform">
        <input name="command" type="hidden" value="act">
        <input name="action" type="hidden" value="rename">
        <input name="server" type="hidden" value="%s">
        <table>
            <tr> 
                <td colspan="2"><label for="rename">rename to:</label></td>
                <td colspan="2"><input type="text" name="newname" value="" /></td>
            </tr>
            <tr> 
                <td colspan="4"><a href="#" id="renamebutton" class="actionbutton">Rename</a></td>
            </tr>
        </table>
    </form>''' % server_name

def display_stats(server_name):
    print '''
    <script type="text/javascript">
        $('.rename').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "display", 
                                      server: $(this).attr("id"), 
                                      page: "rename" },
         function(data){ $('#main').html(data); });
    }));
    $('.update').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "display", 
                                      server: $(this).attr("id"), 
                                      page: $(this).html() },
         function(data){ $('#main').html(data); });
    }));
    </script>'''
    print '<h2>%s</h2>' % 'Server Status'
    instance = mineos.mc(server_name)

    if instance.status() in ['down', 'foreign', 'unclean']:
        print "<h3>%s %s</h3>" % (server_name,
                                  '<a href="#" class="rename" id="%s">(rename)</a><br>' % server_name)
    else:
        print "<h3>%s</h3>" % server_name
    
    print "<h4>server is currently: %s</h4>" % instance.status()
    print '<ul>'
    print '<li><a href="#" class="update" id="%s">%s</a></li>' % (server_name, 'server.properties')
    print '<li><a href="#" class="update" id="%s">%s</a></li>' % (server_name, 'server.config')
    print '</ul>'
    
def display_overview():
    print '''
    <script type="text/javascript">

    $('.updatemc').one("click", (function(event){
        event.preventDefault();
        $('.updatemc').addClass('plaintext');
        $('.updatemc').html("Updating Minecraft Server Jars...");
        $.post("cgi-bin/server.py", { command: "act", 
                                      action: "updatemc",
                                      server: "none"},
        function(data){  $('.updatemc').html("Updating Complete."); });
    }));

     $('.updatemos').one("click", (function(event){
        event.preventDefault();
        $('.updatemos').addClass('plaintext');
        $('.updatemos').html("Updating MineOS...");
        $.post("cgi-bin/server.py", { command: "act", 
                                      action: "updatemos",
                                      server: "none"},
        function(data){  $('.updatemos').html("Update Complete."); });
    }));

    $('.stopall').one("click", (function(event){
        event.preventDefault();
        $('.stopall').html("stopping servers...");
        $('.stopall').addClass('plaintext');
        $.post("cgi-bin/server.py", { command: "act", 
                                      action: "stopall",
                                      server: "none"},
        function(data){  $('.stopall').html("Servers sent stop command."); });
    }));
    $('.forcestop').one("click", (function(event){
        event.preventDefault();
        $('.forcestop').html("killing servers...");
        $('.forcestop').addClass('plaintext');
        $.post("cgi-bin/server.py", { command: "act", 
                                      action: "forcestop",
                                      server: "none"},
        function(data){  $('.forcestop').html("killall java executed."); });
    }));
    
    $('.updatechooser').click( (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "display",
                                      server: "none",
                                      page: "jars" },
         function(data){ $('#main').html(data); });
    }));
    </script>'''
    print '<h1>MineOS Server Overview</h1>'
    print '<pre>'
    print '<b>Minecraft file timestamps</b>:', '<a href="#" class="updatemc">%s</a>' % 'Update Minecraft Server Jars',
    print ' <a href="#" class="updatechooser">%s</a>' % 'Jar selection'
    for filename in [mineos.mc().mineos_config['downloads']['mc_jar'],
                     mineos.mc().mineos_config['downloads']['bukkit_jar'],
                     mineos.mc().mineos_config['downloads']['c10t_tgz']]:
        filepath = os.path.join(mineos.mc().mineos_config['paths']['mc_path'], filename)
        if os.access(filepath, os.F_OK):
            print mineos.mc.list_build_date(filepath), filename
        else:
            print '----------', filename

    filename = mineos.mc().mineos_config['downloads']['canary_jar']
    filepath = os.path.join(mineos.mc().mineos_config['paths']['mc_path'], 'canary', filename)
    if os.access(filepath, os.F_OK):
        print mineos.mc.list_build_date(filepath), filename
    else:
        print '----------', filename
        
    filename = mineos.mc().mineos_config['downloads']['tekkit_jar']
    filepath = os.path.join(mineos.mc().mineos_config['paths']['mc_path'], 'tekkit', filename)
    if os.access(filepath, os.F_OK):
        print mineos.mc.list_build_date(filepath), filename
    else:
        print '----------', filename

    print
    print '<b>MineOS Scripts</b>:', '<a href="#" class="updatemos">%s</a>' % 'Update MineOS'
    print '{:<18}'.format('server.py'), __version__
    import mineos_console
    print '{:<18}'.format('mineos_console.py'), mineos_console.__version__
    print '{:<18}'.format('mineos.py'), mineos.__version__

    print
    print '<b>MineOS Disk Usage</b>:'
    config = mineos.mc().mineos_config

    def sumdirs(base):
        try:
            return sum(os.path.getsize(os.path.join(dirpath,filename)) for dirpath, dirnames, filenames in os.walk(base) for filename in filenames)
        except OSError as e:
            return e       

    print '{:<25}'.format(config['paths']['mc_path']), sumdirs(config['paths']['mc_path']) / 1000000, 'MB'

    for paths in [config['paths']['world_path'],
                  config['paths']['backup_path'],
                  config['paths']['archive_path'],
                  config['paths']['snapshot_path'],
                  config['paths']['import_path'],
                  config['paths']['http_snapshot_path']]:
        try:
            size = sumdirs(paths)
            print '{:<25}'.format(paths), size / 1000000, 'MB'
        except TypeError:
            print size

    print '{:<25}'.format('Approx. free space'), os.statvfs('/').f_bfree * os.statvfs('/').f_frsize / 1024000, 'MB'
    print '<br>All-server actions: <a href="#" class="stopall">Stop</a> <a href="#" class="forcestop">Kill</a>'
    print '</pre>'
        
def display_importer():
    print '''
    <script type="text/javascript">
        $('.import').one("click", (function(event){
        var clicked = $(this);
        event.preventDefault();
        $(clicked).addClass('plaintext');
        $.post("cgi-bin/server.py", { command: "act",
                                      action: "import",
                                      archive: $(clicked).html(),
                                      server: "none"},
         function(data){  $('#main').html(data); });
         $(clicked).html($(clicked).html() + ' -- saving to server: imported');
    }));
    </script>'''
    print '<h2>Available Imports</h2>'
    print '<p>The following archives were located in <span class="green">%s</span>:</p>' % mineos.mc().mineos_config['paths']['import_path']
    print '<p>'
    print '<ul>'
    for archive in mineos.mc.list_imports():
        print '<li><a href="#" class="import">%s</a></li>' % archive
    print '</ul>'
    print '</p>'

def display_jars():
    def selects_mod(mod):
        selects = []
        if mineos.mc().mineos_config['update'][mod] == 'true':
            selects.append('<option value="true" SELECTED>true</option>')
            selects.append('<option value="false">false</option>')
        else:
            selects.append('<option value="true">true</option>')
            selects.append('<option value="false" SELECTED>false</option>')                
        return ' '.join(selects)
    print '''
    <script type="text/javascript">
     $('#updatelist').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", $('#jarform').serialize(),
             function(data){ $('#main').html(data); });
    }));
    </script>
    <h2>Choose which jars to download and update</h2>
    <p>Note, existing downloaded mods marked 'false' will still function! They simply will not be downloaded/updated when
    'Update Minecraft Server Jars' is clicked.</p>
    <form id="jarform">
      <table>
        <tr> 
          <td colspan="2"><label for="pure">pure</label></td>
          <td colspan="2"><select name="pure" id="pure" tabindex="6">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="bukkit">bukkit</label></td>
          <td colspan="2"><select name="bukkit" id="bukkit" tabindex="6">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="tekkit">tekkit</label></td>
          <td colspan="2"><select name="tekkit" id="tekkit" tabindex="6">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="canary">canary</label></td>
          <td colspan="2"><select name="canary" id="canary" tabindex="6">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="c10t">c10t</label></td>
          <td colspan="2"><select name="c10t" id="c10t" tabindex="6">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="4"><a href="#" id="updatelist" class="actionbutton">Update</a></td>
        </tr>
      </table>
      <input name="server" type="hidden" value="none">
      <input name="command" type="hidden" value="act">
      <input name="action" type="hidden" value="updatejars">
    </form>''' % (selects_mod('pure'),
                  selects_mod('bukkit'),
                  selects_mod('canary'),
                  selects_mod('tekkit'),
                  selects_mod('c10t'))

def display_createnew():
    def selects_mod():
        selects = []

        for mods in mineos.mc.list_server_jars():
            if mods == mineos.mc().mineos_config['downloads']['mc_jar']:
                selects.append('<option value="%s" SELECTED>%s</option>' % (mods, mods))
            else:
                selects.append('<option value="%s">%s</option>' % (mods, mods))
        return ' '.join(selects)
    
    print '''
    <script type="text/javascript">
     $('#createserver').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", $('#newserver').serialize(),
             function(data){ $('#main').html(data); });
    }));
    </script>
    <h2>Create a new Minecraft Server</h2>
    <form id="newserver">
      <table>
        <tr> 
          <td colspan="2"><label for="server">Server Name</label></td>
          <td colspan="2"><input type="text" name="server" id="server" tabindex="1" /></td>
        </tr>
        <tr> 
          <td colspan="4"><em>server names may not contain spaces or non-alphanumerics.</em></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="port">Port</label></td>
          <td colspan="2"><input type="text" name="port" id="port" tabindex="2" value="25565" /></td>
        </tr>
        <tr> 
          <td colspan="4"><em>non-default ports will need to be opened in the iptables firewall</em></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="max_players">Max Players</label></td>
          <td colspan="2"><input type="text" name="max_players" id="max_players" tabindex="3" value="20" /></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="max_players">RAM</label></td>
          <td colspan="2"><input type="text" name="mem" id="mem" tabindex="4" value="1024" /></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="server_jar">Minecraft Jar</label></td>
          <td colspan="2"><select name="server_jar" id="server_jar" tabindex="5">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2">&nbsp</td>
          <td colspan="2"></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="level_seed">level-seed</label></td>
          <td colspan="2"><input type="text" name="level_seed" id="level_seed" tabindex="10" value="" /></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="gamemode">gamemode</label></td>
          <td colspan="2"><select name="gamemode" id="gamemode" tabindex="">
              <option value="0" SELECTED>Survival (0)</option>
              <option value="1">Creative (1)</option>
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="level_type">level-type</label></td>
          <td colspan="2"><select name="level_type" id="level_type" tabindex="">
              <option value="DEFAULT" SELECTED>DEFAULT</option>
              <option value="FLAT">FLAT</option>
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="difficulty">difficulty</label></td>
          <td colspan="2"><select name="difficulty" id="difficulty" tabindex="">
              <option value="0">Peaceful (0)</option>
              <option value="1" SELECTED>Easy (1)</option>
              <option value="2">Normal (2)</option>
              <option value="3">Hard (3)</option>
            </select></td>
        </tr>    
        <tr> 
          <td colspan="2">&nbsp</td>
          <td colspan="2"></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="freq_archive">Archive</label></td>
          <td colspan="2"><select name="freq_archive" id="freq_archive" tabindex="6">
              <option value="none">none</option>
              <option value="hourly">hourly</option>
              <option value="daily">daily</option>
              <option value="weekly">weekly</option>
              <option value="monthly">monthly</option>
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="freq_backup">Backup</label></td>
          <td colspan="2"><select name="freq_backup" id="freq_backup" tabindex="7">
              <option value="none">none</option>
              <option value="hourly">hourly</option>
              <option value="daily">daily</option>
              <option value="weekly">weekly</option>
              <option value="monthly">monthly</option>
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="freq_map">Map</label></td>
          <td colspan="2"><select name="freq_map" id="freq_map" tabindex="8">
              <option value="none">none</option>
              <option value="hourly">hourly</option>
              <option value="daily">daily</option>
              <option value="weekly">weekly</option>
              <option value="monthly">monthly</option>
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="restore">Restore on Reboot</label></td>
          <td colspan="2"><select name="restore" id="restore" tabindex="6">
            <option value="true">true</option>
            <option value="false" SELECTED>false</option>
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="start">Start on Reboot</label></td>
          <td colspan="2"><select name="start" id="start" tabindex="6">
            <option value="true">true</option>
            <option value="false" SELECTED>false</option>
            </select></td>
        </tr>
        <tr> 
          <td colspan="4"><a href="#" id="createserver" class="actionbutton">Create Server</a></td>
        </tr>
      </table>
      <input name="command" type="hidden" value="act">
      <input name="action" type="hidden" value="create">
    </form>''' % selects_mod()

def display_server_config(server_name):
    def selects_mod():
        selects = []

        for mods in mineos.mc.list_server_jars():
            if mods == mineos.mc(server_name).server_config['java']['server_jar']:
                selects.append('<option value="%s" SELECTED>%s</option>' % (mods, mods))
            else:
                selects.append('<option value="%s">%s</option>' % (mods, mods))
        return ' '.join(selects)   

    def selects_crontab(server_name, crontype):
        selects = []

        for mods in ['none', 'hourly', 'daily', 'weekly', 'monthly']:
            if mods == instance.server_config['crontabs']['freq_' + crontype]:
                selects.append('<option value="%s" SELECTED>%s</option>' % (mods, mods))
            else:
                selects.append('<option value="%s">%s</option>' % (mods, mods))
        return ' '.join(selects)

    def selects_onboot(server_name, activity):
        selects = []

        newinst = mineos.mc(server_name)
        try:
            if newinst.server_config['onreboot'][activity] == 'true':
                selects.append('<option value="true" SELECTED>true</option>')
                selects.append('<option value="false">false</option>')
            else:
                selects.append('<option value="true">true</option>')
                selects.append('<option value="false" SELECTED>false</option>')
        except KeyError:
            raise mineos.NoOnRebootSectionException(server_name,
                                                    os.path.join(newinst.cwd, 'server.config'))
            selects.append('<option value="true">true</option>')
            selects.append('<option value="false" SELECTED>false</option>')           
        return ' '.join(selects)
        
    instance = mineos.mc(server_name)
    print '''
    <script type="text/javascript">
     $('.updatesc').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", $('#updateserver').serialize(),
             function(data){ $('#main').html(data); });
    }));
    </script>
    <h2>server.config for %s</h2>
    <form id="updateserver">
        <input name="command" type="hidden" value="act">
        <input name="action" type="hidden" value="update_sc">
        <input name="server" type="hidden" value="%s">
      <table>
        <tr> 
          <td colspan="2"><label for="port">Server Port</label></td>
          <td colspan="2"><input type="text" name="port" id="port" tabindex="2" value="%s" /></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="max_players">Max Players</label></td>
          <td colspan="2"><input type="text" name="max_players" id="max_players" value="%s" tabindex="3" /></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="max_players">RAM</label></td>
          <td colspan="2"><input type="text" name="mem" id="mem" value="%s" tabindex="4" /></td>
        </tr>
        <tr> 
          <td colspan="2">&nbsp</td>
          <td colspan="2"></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="mod">Server Jar</label></td>
          <td colspan="2"><select name="server_jar" id="server_jar" tabindex="5">
              %s
                          </select>
          </td>
        </tr>
        <tr> 
          <td colspan="2"><label for="server_jar_args">Jar Arguments</label></td>
          <td colspan="2"><input type="text" name="server_jar_args" id="server_jar_args" value="%s" tabindex="9" /></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="java_tweaks">Java Tweaks</label></td>
          <td colspan="2"><input type="text" name="java_tweaks" id="java_tweaks" value="%s" tabindex="9" /></td>
        </tr>
        <tr> 
          <td colspan="2">&nbsp</td>
          <td colspan="2"></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="freq_archive">Archive</label></td>
          <td colspan="2"><select name="freq_archive" id="freq_archive" tabindex="6">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="freq_backup">Backup</label></td>
          <td colspan="2"><select name="freq_backup" id="freq_backup" tabindex="7">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="freq_map">Map</label></td>
          <td colspan="2"><select name="freq_map" id="freq_map" tabindex="8">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2">&nbsp</td>
          <td colspan="2"></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="restore">Restore on Reboot</label></td>
          <td colspan="2"><select name="restore" id="restore" tabindex="6">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="2"><label for="start">Start on Reboot</label></td>
          <td colspan="2"><select name="start" id="start" tabindex="6">
              %s
            </select></td>
        </tr>
        <tr> 
          <td colspan="4"><a href="#" class="updatesc actionbutton">Update</a></td>
        </tr>
      </table>
    </form>''' %(server_name, server_name,
                 instance.server_config['minecraft']['port'],
                 instance.server_config['minecraft']['max_players'],
                 instance.server_config['minecraft']['mem'],
                 selects_mod(),
                 instance.server_config['java']['server_jar_args'],
                 instance.server_config['java']['java_tweaks'],
                 selects_crontab(server_name, 'archive'),
                 selects_crontab(server_name, 'backup'),
                 selects_crontab(server_name, 'map'),
                 selects_onboot(server_name, 'restore'),
                 selects_onboot(server_name, 'start'))

def display_server_properties(server_name):
    print '''
    <script type="text/javascript">
     $('.updatesp').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", $('#changevalues').serialize(),
             function(data){ $('#main').html(data); });
    }));
    </script>'''

    print '<h2>server.properties for %s</h2>' % server_name

    instance = mineos.mc(server_name)
    filename = os.path.join(instance.mineos_config['paths']['world_path'], server_name, 'server.properties')
    status = instance.status()

    if status in ['up', 'down', 'foreign', 'unclean']:
        print '''<form name="changevalues" id="changevalues">
                    <input name="command" type="hidden" value="act">
                    <input name="action" type="hidden" value="update_sp">
                    <input name="server" type="hidden" value="%s">
                     <table>''' % server_name

        for key, value in mineos.mc.attribute_list(filename):
            print '''
                        <tr> 
                            <td colspan="2"><label for="%s">%s</label></td>
                            <td colspan="2"><input type="text" name="%s" id="%s" value="%s" /></td>
                        </tr>''' % (key.replace('-', '_'),
                                key,
                                key.replace('-', '_'),
                                key.replace('-', '_'),
                                value)
        print '''       <tr>
                            <td colspan="4"><a href="#" class="updatesp actionbutton">Update</a></td>
                        </tr>
                    </table>
                 </form>'''

def display_restore():
    print '''
    <script type="text/javascript">
    $('.restore').one("click", (function(event){
        event.preventDefault();
        $.post("cgi-bin/server.py", { command: "act",
                                      action: "restore",
                                      server: $(this).attr("id"),
                                      steps: $(this).html() },
         function(data){ $('#main').html(data); });
    }));
    </script>'''
    print '<h2>%s</h2>' % 'Incremental Backups'

    print '<p>The following backup states were found in <span class="green">%s</a>:</p>' % mineos.mc().mineos_config['paths']['backup_path']
    print '<p><i>Click an increment to restore a server to a previous state.</i><br>Servers currently running cannot be restored until stopped.</p>'

    for server, port, status in mineos.mc.ports_reserved_backup():
        print '<h4>%s</h4>' % server
        try:
            output = mineos.mc(server).list_backups()
            print '<ol class="backupli">'
            for index, item in enumerate(output):
                count = len(output) - index - 2
                if not index:
                    print '<li>%s</li>' % item,
                elif count < 0:
                    pass
                else:
                    if mineos.mc(server).status() != 'up':
                        print '<li><a href="#" class="restore" id="%s">%s</a> %s</li>' % (server,
                                                                                          str(count) + 'B',
                                                                                          item)
                    else:
                        print '<li>%s %s</li>' % (str(count) + 'B',
                                                  item)
            
        except:
            print '<li>None</li>'
        print '</ol>'
        
def act_update_sp(form):
    sp = os.path.join(mineos.mc().mineos_config['paths']['world_path'], form['server'], 'server.properties')
    sc = os.path.join(mineos.mc().mineos_config['paths']['world_path'], form['server'], 'server.config')
    
    for key in form.keys():
        mineos.mc.attribute_change(sp, key.replace('_', '-'), form[key], form['server'])
        
        if key == 'server_port':
            mineos.mc.config_alter(sc, 'minecraft', 'port', form[key], form['server'])
        elif key == 'max_players':
            mineos.mc.config_alter(sc, 'minecraft', key, form[key], form['server'])
            
    print '<pre>'
    for key, value in mineos.mc.attribute_list(sp):
        print '{:<15}'.format(key), '{:<15}'.format(value)
    print '</pre>'

def act_update_sc(form):
    sp = os.path.join(mineos.mc().mineos_config['paths']['world_path'], form['server'], 'server.properties')
    sc = os.path.join(mineos.mc().mineos_config['paths']['world_path'], form['server'], 'server.config')
    
    for key in form.keys():
        if key in ['port', 'max_players', 'mem']:
            mineos.mc.config_alter(sc, 'minecraft', key, form[key], form['server'])
        elif key in ['freq_archive', 'freq_backup', 'freq_map']:
            mineos.mc.config_alter(sc, 'crontabs', key, form[key], form['server'])
        elif key in ['server_jar', 'server_jar_args', 'java_tweaks']:
            mineos.mc.config_alter(sc, 'java', key, form[key], form['server'])
        elif key in ['restore', 'start']:
            mineos.mc.config_alter(sc, 'onreboot', key, form[key], form['server'])

        if key == 'port':
            mineos.mc.attribute_change(sp, 'server-port', form[key], form['server'])
        elif key == 'max_players':
            mineos.mc.attribute_change(sp, 'max-players', form[key], form['server'])

    for key in form.keys():
        print "%s = %s<br>" % (key, form[key])        

def act_update_jars(form):
    configfile = os.path.join(mineos.mc().mc_path, 'mineos.config')
    for key in form.keys():
        if key not in ['server', 'command', 'action']:
            mineos.mc.config_alter(configfile, 'update', key, form[key], 'None')
        
    for key in form.keys():
        print "%s = %s<br>" % (key, form[key])

form = cgi_to_dict(cgi.FieldStorage(keep_blank_values=1))

#print form

try:
    if form['command'] == 'display':
        if form['page'] == 'status':
            display_status()
        elif form['page'] == 'console':
            display_logdump()
        elif form['page'] == 'logs':
            display_mineoslogdump()
        elif form['page'] in ['backup', 'archive', 'map']:
            display_bam(form['page'])
        elif form['page'] == 'restore':
            display_restore()
        elif form['page'] == 'rename':
            display_rename(form['server'])
        elif form['page'] == 'stats':
            display_stats(form['server'])
        elif form['page'] == 'import':
            display_importer()
        elif form['page'] == 'createnew':
            display_createnew()
        elif form['page'] == 'server.properties':
            display_server_properties(form['server'])
        elif form['page'] == 'server.config':
            display_server_config(form['server'])
        elif form['page'] == 'about':
            display_about()
        elif form['page'] == 'initial':
            display_initial()
        elif form['page'] == 'overview':
            display_overview()
        elif form['page'] == 'crontabs':
            display_crontabs()
        elif form['page'] == 'jars':
            display_jars()
        else:
            display_initial()
        
    elif form['command'] == 'act':
        instance = mineos.mc(form['server'])
        if form['action'] == 'create':
            instance.create(form)
            display_status()
        elif form['action'] == 'start':
            instance.start()
        elif form['action'] == 'stop':
            instance.stop()
        elif form['action'] == 'stopall':
            mineos.mc.stopall()
        elif form['action'] == 'forcestop':
            mineos.mc.forcestop()
        elif form['action'] == 'clean':
            instance.clean()
            display_status()
        elif form['action'] == 'backup':
            instance.backup()
        elif form['action'] == 'archive':
            instance.archive()
        elif form['action'] == 'restore':
            instance.restore(form['steps'], True)
        elif form['action'] == 'map':
            instance.mapworld()
        elif form['action'] == 'rename':
            instance.rename(form['newname'])
        elif form['action'] == 'import':
            mineos.mc('imported').importworld(form['archive'])
        elif form['action'] == 'updatemc':
            mineos.mc.update()
        elif form['action'] == 'updatemos':
            mineos.mc.update_mineos()
        elif form['action'] == 'logdump':
            instance.log_dump()
        elif form['action'] == 'mineoslogdump':
            instance.mineoslog_dump()
        elif form['action'] == 'log_archive':
            instance.log_archive()
        elif form['action'] == 'update_sp':
            act_update_sp(form)
            print '(%s) update server.properties complete' % form['server']
        elif form['action'] == 'update_sc':
            act_update_sc(form)
            print '(%s) update server.config complete' % form['server']
        elif form['action'] == 'consolecommand':
            mineos.mc(form['server']).command(form['argument'])
        elif form['action'] == 'updatejars':
            act_update_jars(form)
except KeyError:
    print 'invalid number of arguments'
except:
    pass
