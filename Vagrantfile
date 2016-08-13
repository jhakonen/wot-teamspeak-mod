# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'etc'

# Adjust this to match your environment
WOTPATH = "C:\\Games\\World_of_Tanks"

Vagrant.configure("2") do |config|
    config.vm.box = "jhakonen/windows-10-n-pro-en-x86_64"
    config.vm.guest = :windows
    config.vm.communicator = "winrm"
    config.vm.synced_folder WOTPATH, "/world_of_tanks"
    config.vm.provision "shell" do |s|
    	s.path = "vagrant-bootstrap.ps1"
    	s.args = "-FromVagrant"
    end
    config.vm.provision :reload

    config.vm.provider "virtualbox" do |vb|
        vb.cpus = Etc.nprocessors
    end
end
