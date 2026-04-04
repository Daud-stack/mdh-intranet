# Run Collabora CODE (Collabora Online Development Edition) in Docker
# Port 9980 is used for the editor
# We disable SSL for local development
# We allow localhost and host.docker.internal as WOPI hosts

docker run -t -d -p 9980:9980 `
    -v "C:\collabora\coolwsd.xml:/etc/coolwsd/coolwsd.xml" `
    -e "domain=host\.docker\.internal.*|localhost.*|10\.232\.190\.161.*" `
    -e "username=admin" `
    -e "password=secret" `
    -e "extra_params=--o:ssl.enable=false --o:alias_groups.mode=first" `
    --restart always `
    --name collabora_code `
    collabora/code

Write-Host "Collabora CODE started on port 9980"
Write-Host "URL: http://localhost:9980"
