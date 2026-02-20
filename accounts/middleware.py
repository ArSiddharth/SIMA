class SessionMiddleware:
    def __init__(self, get_response):
        self.get_response=get_response
   
    def __call__(self, request):
        if request.user.is_authenticated and request.session.get('logged_in'):
            pass
        elif request.user.is_authenticated:
            request.session['logged_in']=True
       
        response=self.get_response(request)
        return response
 