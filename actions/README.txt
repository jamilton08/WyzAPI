all notificiations that plans to have a respond actions must inherit
action responce.

build_response_ini.py will hold the initiation and the response
functions which tell us what type of record will initiate them

the models that inhereit such ActionResponse class must have
functions that handle_actions_queries and handle_actions_response which
will give us which users recieve the respond query and who recieve the respond
notification after handled
