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

	# from https://support.teamspeakusa.com/index.php?/Knowledgebase/Article/View/44/16/which-ports-does-the-teamspeak-3-server-use
	config.vm.network :forwarded_port, guest: 9987, host: 9987, id: "ts-server-voice", protocol: "udp"
	config.vm.network :forwarded_port, guest: 10011, host: 10011, id: "ts-server-serverquery", protocol: "tcp"
	config.vm.network :forwarded_port, guest: 30033, host: 30033, id: "ts-server-filetransfer", protocol: "tcp"
	config.vm.network :forwarded_port, guest: 41144, host: 41144, id: "ts-server-tsdns", protocol: "tcp"
end
