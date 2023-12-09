import graphene
import stock_data.schema

class Query(stock_data.schema.Query, graphene.ObjectType):
	pass

schema = graphene.Schema(query=Query)