To use the application via Postman, follow the steps:

1\. Hit the GET request to hit the application url( eg: http://localhost:8000)

2\. Click on Import and paste this code """ 
    curl --path-as-is -i -s -k -X $'POST' \
    -H $'Host: localhost:8000' -H $'Content-Length: 128' -H $'Cache-Control: max-age=0' -H $'sec-ch-ua: \"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"' -H $'sec-ch-ua-mobile: ?0' -H $'sec-ch-ua-platform: \"Windows\"' -H $'Accept-Language: en-US,en;q=0.9' -H $'Origin: http://localhost:8000' -H $'Content-Type: application/x-www-form-urlencoded' -H $'Upgrade-Insecure-Requests: 1' -H $'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36' -H $'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' -H $'Sec-Fetch-Site: same-origin' -H $'Sec-Fetch-Mode: navigate' -H $'Sec-Fetch-User: ?1' -H $'Sec-Fetch-Dest: document' -H $'Referer: http://localhost:8000/accounts/login/?next=/' -H $'Accept-Encoding: gzip, deflate, br' -H $'Connection: keep-alive' \
    -b $'csrftoken=Zz4c8O8OldASwUEzjR4iHhtmRlSPA8kn' \
    --data-binary $'csrfmiddlewaretoken=sutipZmDYuNildOzadlaslL2b8Eu198ihTnknDkh9xd0HXiYjUfiZs4eSjm9r7iv&username=admin&password=pass%401234&button=' \
    $'http://localhost:8000/accounts/login/?next=/'
 """

3\. Copy the csrf token generated in Cookie from response of first request and also copy the csrfmiddlewaretoken which you will get from raw html response of first request.

4\. Hit the POST request to application login(http://localhost:8000/account/login) add Cookie as key in Header section and in the value write csrftoken=<csrftoken you copied from first request> without "<>" and in body add the fields

( csrfmiddlewaretoken=<value you copied from raw response of first request>, username, password, button) 




**Note**: You must add csrfmiddlewaretoken in every endpoint and always use the updated value of csrfmiddlewaretoken and csrf token. Remove "<>" everywhere.

