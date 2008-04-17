#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import cgi
import wsgiref.handlers
import string

import os
from google.appengine.ext.webapp import template

from google.appengine.ext import db 
from google.appengine.api import users
from google.appengine.ext import webapp


#Model of the message
class Message(db.Model):
    user = db.UserProperty() #creator
    name = db.StringProperty(required=True) #name of the message, used as id
    content = db.TextProperty()  
    date = db.DateTimeProperty(auto_now_add=True)


#route /
class MainPage(webapp.RequestHandler):
    def get(self):
        self.redirect('/messages')   #calls the list method


#Rest controller  
class MessagesController(webapp.RequestHandler):
    #shows all the messages
    #route: GET /messages
    def list(self):
        messages = Message.all()
        messages.order("-date")  
        self.render('templates/index.html', messages=messages)
    
    #shows the given message
    #route: GET  /messages/message_name
    def show(self,message):
        self.render("templates/showMessage.html", message)

    #shows the new form
    #route: GET  /messages/new
    def new(self):
        self.render("templates/newMessage.html")

    #shows the edit form
    #route: GET  /messages/:message_name/edit
    def edit(self,message):
        self.render("templates/editMessage.html", message)

    #creates the message and puts it into the datastore
    #route: POST  /messages
    def create(self): 
        if self.request.get('name'):
            message=Message(name = self.request.get('name')  )  #new message
            if users.get_current_user():
                message.user = users.get_current_user()
            message.content = self.request.get('content')
            message.put()   
            self.redirect('/messages/'+message.name)   #redirects to list 
        else:  
            self.response.out.write('<div class="message"><b>ERROR:</b> message name is empty.</div>')

    #updates the given message
    #route: PUT  /messages/message_id
    def update(self,message):
        message.name = self.request.get('name')
        message.content = self.request.get('content')
        message.put()
        self.redirect('/messages/'+message.name) #redirects to show

    #deletes the given message
    #route: PUT  /messages/message_id
    def destroy(self,message):
        message.delete();
        self.redirect('/messages')  #redirects to list 

    #get method: selects the action (list, show, edit or  new) depending of the url_data
    def get(self,url_data): 
        #gets message
        action = self.getAction(url_data)
        if(url_data and action != "new") :
            message=self.getMessage(self.message_name)  
        if action == "show":
            self.show(message)
        elif action == "edit": 
            self.edit(message)
        elif action == "new":
            self.new()
        elif action == "list":
            self.list()
        else:
            self.response.out.write('<div class="message"><b>ERROR:</b> action=%s does not exists.</div>' % action)

    #gets the message object from de datastore
    def getMessage(self,message_name):
        messages = Message.all()
        return messages.filter("name =",message_name).fetch(1)[0]

    #gets the action depending of the url_data and gets the message name if  needed. 
    #TODO: make two functions getAction and getName.
    def getAction(self,url_data):
        message_name=url_data[1:]  #remove the first "/"
        parts=string.split(message_name,"/")  #if /message/name/edit or /message/new 
        self.message_name=parts[0]
        if(len(parts) == 1):      # /messages/???
             if(parts[0] == "new"):   # /messages/new
                 action="new"
             elif parts[0] == "":     # /messages or /messages/
                 action="list"
             else:   			     # /messages/message_id
                 action="show"
        else:			   #/messages/???/edit
            if parts[1] == "edit":
                action="edit"   
            else: 
                action=parts[1]    #error
        return action

     #post method: selects the action (create, update, destroy) depending of the _verb
     #REMEMBER: you MUST use the hidden _verb=put in the form of the edit page.  see editMessage.html
     #REMEMBER: you MUST use the special link with js to call the destroy action.  see showMessage.html
    def post(self,message_name):
        _verb=self.request.get('_verb')
        if _verb == "":    #POST
             self.create()
        else:
            message=self.getMessage(message_name[1:])  
            if _verb == "delete":
                self.destroy(message)
            elif _verb == "put":
                self.update(message)
            else:
                self.response.out.write('<div class="message"><b>ERROR:</b> action=%s does not exists.</div>' % action)
 
    #Calls the templates and renders the response page
    def render(self,template_file,message=None,messages=None):
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
                                    
        template_values={'message':message,
                         'messages':messages,
                         'url':url,
                         'url_linktext':url_linktext
                         }
        path = os.path.join(os.path.dirname(__file__), template_file)
        self.response.out.write(template.render(path, template_values))


#------------------------
def main():
    application = webapp.WSGIApplication(
                                       [('/', MainPage),
				       ('/messages(|/.*)',MessagesController)],  #rest route
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
