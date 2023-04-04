from marshmallow import Schema, fields


class AdminSchema(Schema):
    id = fields.Int(required=False)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class QuestionSchema(Schema):
    id = fields.Int(required=True, dump_only=True)
    word = fields.Str(required=True)
    description = fields.Str(required=True)

class QuestionListSchema(Schema):
    questions = fields.Nested(QuestionSchema, many=True)


class SearchWordSchema(Schema):
    search = fields.Str()
