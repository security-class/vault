var spec = {
    "swagger": "2.0",
    "info": {
        "version": "1.0.0",
        "title": "SAM Rest API",
        "description": "SAM Swagger"
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ],
    "consumes": [
        "application/json",
        "text/xml"
    ],
    "produces": [
        "application/json",
        "text/html"
    ],
    "paths": {
        "/users": {
            "get": {
                "responses": {
                    "200": {
                        "description": "List all users",
                        "schema": {
                            "title": "Users",
                            "type": "array",
                            "items": {
                                "$ref": "#/definitions/User"
                            }
                        }
                    }
                }
            },
            "post": {
                "parameters": [
                    {
                        "name": "user",
                        "in": "body",
                        "description": "User name",
                        "schema": {
                            "first_name": "first_name",
                            "last_name": "last",
                            "email": "email",
                            "password": "password"
                        },
                        "required": true
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Created User"
                    },
                    "409": {
                        "description": "User already exist",
                        "schema": {
                            "title": "respone",
                            "type": "object",
                            "items": {
                                "$ref": "#/definitions/error"
                            }
                        }
                    }
                }
            }
        },
        "/users/{id}": {
            "get": {
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "type": "integer",
                        "description": "ID of the User",
                        "required": true
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Sends the user with the ID"
                    },
                    "400": {
                        "description": "User doesn't exist",
                        "schema": {
                            "title": "respone",
                            "type": "object",
                            "items": {
                                "$ref": "#/definitions/error"
                            }
                        }
                    }
                }
            },
            "put": {
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "type": "integer",
                        "description": "ID of the User",
                        "required": true
                    },
                    {
                        "in": "body",
                        "name": "user",
                        "description": "User details",
                        "required": true,
                        "schema": {
                            "$ref": "#/definitions/User"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Updates the user with the id, and replaces with Body"
                    },
                    "404": {
                        "description": "User not found",
                        "schema": {
                            "title": "respone",
                            "type": "object",
                            "items": {
                                "$ref": "#/definitions/error"
                            }
                        }
                    }
                }
            },
            "delete": {
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "type": "integer",
                        "description": "ID of the User",
                        "required": true
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Deletes the user with the ID"
                    },
                    "204": {
                        "description": "User does not exist",
                        "schema": {
                            "title": "respone",
                            "type": "object",
                            "items": {
                                "$ref": "#/definitions/error"
                            }
                        }
                    }
                }
            }
        },
        "/vault/{id}": {
            "get": {
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "type": "integer",
                        "description": "id of the User",
                        "required": true
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Gets the user vault with the ID"
                    },
                    "400": {
                        "description": "User doesn't exist",
                        "schema": {
                            "title": "respone",
                            "type": "object",
                            "items": {
                                "$ref": "#/definitions/error"
                            }
                        }
                    }
                }
            },
            "post": {
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "type": "integer",
                        "description": "ID of the User",
                        "required": true
                    },
                    {
                        "in": "body",
                        "name": "vault",
                        "description": "entries of the user",
                        "required": true,
                        "schema": {
                            "$ref": "#/definitions/vault"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "create an entry"
                    },
                    "400": {
                        "description": "",
                        "schema": {
                            "title": "respone",
                            "type": "object",
                            "items": {
                                "$ref": "#/definitions/error"
                            }
                        }
                    }
                }
            }
        }
    },
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "first": {
                    "type": "string"
                },
                "last": {
                    "type": "string"
                },
                "email": {
                    "type": "string"
                },
                "password": {
                    "type": "string"
                },
                "vault": {
                    "$ref": "#/definitions/vault"
                }
            }
        },
        "vault": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "array",
                "items": {
                    "$ref": "#/definitions/entry"
                    }
                }
            }
        },
        "entry": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string"
                },
                "password": {
                    "type": "string"
                },
                "domain": {
                    "type": "string"
                }
            }
        },
        "error": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string"
                }
            }
        }
    }
};