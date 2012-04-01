Added Features
=========

 * Tekkit support
 * Ability to choose to use c10t, pigmap, or both for mapping
 * Map and Backup commands notify the server with the say command

Instructions
=============

These scripts are modifications to the ones included in [MineOS Crux](http://minecraft.codeemo.com/). It's possible to use them elsewhere but they work with the systems in place with the distribution.
 
To install, run the following commands as root:

```shell
# cd /usr/games/minecraft/
# wget https://github.com/Fsmv/MineOSCrux-Fork/tarball/master
# tar -xvf master   
# cd Fsmv-MineOSCrux-Fork-[commit hash]
# mv *.py ../
# cd ../
# rm -rf Fsmv-MineOSCrux-Form-[commit hash]/
```

Finally, edit the config files /usr/games/minecraft/mineos.config and /home/mc/servers/[server name]/server.config to match the example scripts
 
About
=====

This is a fork of the [MineOS Crux](http://minecraft.codeemo.com/) Linux distribution built for hosting Minecraft servers. I have made a post announcing it on the Google group for the distribution which can be found [here](https://groups.google.com/forum/#!activity/mineos/aGElX40KndYJ/mineos/oY6r6Jt-M4g/6j7yQ3RmWqkJ).
