$env:PATH="$env:PATH;C:\Program Files\7-Zip"
Remove-Item -Recurse -ErrorAction SilentlyContinue -Path $env:TEMP\deps
New-Item -ItemType directory -Path $env:TEMP\deps
Push-Location -Path $env:TEMP\deps

# Create wotmod package for littletable
pip download littletable==0.10
7z -y e littletable-0.10.tar.gz
7z -y x littletable-0.10.tar
Push-Location -Path littletable-0.10
python setup.py bdist_wotmod `
    --install-lib=res/scripts/common `
    --author-id=net.sourceforge.ptmcg `
    --dist-dir=$PSScriptRoot
Pop-Location

# Create wotmod package for Promise
pip download promise==2.0.1
7z -y e promise-2.0.1.tar.gz
7z -y x promise-2.0.1.tar
Push-Location -Path promise-2.0.1
python setup.py bdist_wotmod `
    --install-lib=res/scripts/common `
    --author-id=com.github.syrusakbary `
    --dist-dir=$PSScriptRoot
Pop-Location

# Create wotmod package for six (dependency of Promise)
pip download six==1.11.0 --no-binary=:all:
7z -y e six-1.11.0.tar.gz
7z -y x six-1.11.0.tar
Push-Location -Path six-1.11.0
python setup.py bdist_wotmod `
    --install-lib=res/scripts/common `
    --author-id=com.github.benjaminp `
    --dist-dir=$PSScriptRoot
Pop-Location

# Create wotmod package for typing (dependency of Promise)
pip download typing==3.6.2 --no-binary=:all:
7z -y e typing-3.6.2.tar.gz
7z -y x typing-3.6.2.tar
Push-Location -Path typing-3.6.2
python setup.py bdist_wotmod `
    --install-lib=res/scripts/common `
    --author-id=org.python `
    --dist-dir=$PSScriptRoot
Pop-Location

# Create wotmod package for pydash
pip download pydash==4.2.1 --no-binary=:all:
7z -y e pydash-4.2.1.tar.gz
7z -y x pydash-4.2.1.tar
Push-Location -Path pydash-4.2.1
python setup.py bdist_wotmod `
    --install-lib=res/scripts/common `
    --author-id=com.github.dgilland `
    --dist-dir=$PSScriptRoot
Pop-Location

Pop-Location
