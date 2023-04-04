from hashlib import sha256

from aiohttp.web import HTTPForbidden, HTTPUnauthorized
from aiohttp.web_exceptions import HTTPConflict
from aiohttp_apispec import request_schema, response_schema, docs, querystring_schema
from aiohttp_session import new_session

from kts_backend.admin.mixins import AuthRequiredMixin
from kts_backend.admin.schemes import AdminSchema, QuestionSchema, QuestionListSchema, SearchWordSchema
from kts_backend.web.app import View
from kts_backend.web.utils import json_response


class AdminLoginView(View):
    @docs(tags=["admins"],
          summary="Method for admin login",
          description="Method checks the email and password and if they are correct, then authorizes the admin.")
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        email = self.data["email"]
        existed_admin = await self.store.admins.get_by_email(email)

        if not existed_admin:
            raise HTTPForbidden(reason='no admin with the email')

        password = self.data["password"]
        if existed_admin.password != sha256(password.encode()).hexdigest():
            raise HTTPForbidden(reason='invalid password')
        response_data = AdminSchema().dump(existed_admin)

        session = await new_session(request=self.request)
        session["admin"] = response_data

        return json_response(data=response_data)


class QuestionAddView(AuthRequiredMixin, View):
    @docs(tags=["questions"],
          summary="Method for add question",
          description="Add new question in database, question includes word and description")
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema, 200)
    async def post(self):
        word, description = self.data['word'], self.data['description']

        if await self.store.admins.get_question_by_word(word=word) is not None:
            raise HTTPConflict
        question = await self.store.admins.create_question(word=word, description=description)
        return json_response(data=QuestionSchema().dump(question))


class QuestionListView(AuthRequiredMixin, View):
    @docs(tags=["questions"],
          summary="Method for get questions list",
          description="Get questions list from database all or by a search word")
    @querystring_schema(SearchWordSchema)
    @response_schema(QuestionSchema, 200)
    async def get(self):
        search_word = self.data.get('search')
        questions = await self.store.admins.question_list(search_word)
        return json_response(data=QuestionListSchema().dump({"questions": questions}))


class Hello(View):
    async def get(self):
        response_data = "Hello"

        return json_response(data=response_data)
