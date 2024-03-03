<p align="center">
  <img src="https://github.com/Splash-Media-Co/server/assets/103071021/8baf6086-d31a-4404-be8a-07c6fc0aed1f)https://github.com/Splash-Media-Co/server/assets/103071021/8baf6086-d31a-4404-be8a-07c6fc0aed1f"/>
</p>

<h1 align="center">Backend server for Splash</h1>
<h4 align="center">This is the server that runs all of Splash.</h4>

---

# Splash Server Documentation
## Overview

The Splash server is a backend system responsible for handling various commands from clients, such as posting messages, authentication, retrieving posts, and account creation. This document provides comprehensive documentation for each supported command, including usage instructions, parameters, examples, and potential errors. 

> [!WARNING]  
> This server is still in development. Expect breaking changes, bugs, and lots of unstable stuff.

## Commands

### 1. `direct`

#### Description
The `direct` command enables clients to perform direct actions such as posting messages, deleting posts, or editing posts.

#### Parameters
- `type`: Specifies the type of action to perform (`post`, `delete`, or `edit`).
- `uid`: Unique identifier of the post to perform the action on.
- `edit`: New content for the post if the action is editing.
- `attachment`: Optional attachment file name for posting.

#### Usage
- To post a message:
  ```json
  {
    "cmd": "direct",
    "val": {
      "cmd": "post",
      "val": {
        "type": "send",
        "p": "Hello, world!",
        "attachment": "image.png"
      }
    }
  }
  ```

- To delete a post:
  ```json
  {
    "cmd": "direct",
    "val": {
      "cmd": "post",
      "val": {
        "type": "delete",
        "uid": "123456789"
      }
    }
  }
  ```

- To edit a post:
  ```json
  {
    "cmd": "direct",
    "val": {
      "cmd": "post",
      "val": {
        "type": "edit",
        "uid": "123456789",
        "edit": "Updated message"
      }
    }
  }
  ```

#### Possible Errors
- Rate Limit Exceeded
- Invalid JSON Payload
- Authentication Failure
- Moderation Flag
- Post Not Found
- Not Authorized
- Unexpected Error

### 2. `auth`

#### Description
The `auth` command is used to authenticate a user.

#### Parameters
- `pswd`: The password associated with the user's account.

#### Usage
```json
{
  "cmd": "auth",
  "val": {
    "pswd": "password123"
  }
}
```

#### Possible Errors
- Invalid Password
- User Doesn't Exist

### 3. `retrieve`

#### Description
The `retrieve` command is used to retrieve posts.

#### Parameters
- `type`: Specifies the type of retrieval (`latest` currently supported).
- `c`: Chat ID or identifier for the conversation.
- `o`: Offset value for retrieving posts.

#### Usage
```json
{
  "cmd": "retrieve",
  "val": {
    "type": "latest",
    "c": "chat_id",
    "o": 0
  }
}
```

#### Possible Errors
- Authentication Failure

### 4. `genaccount`

#### Description
The `genaccount` command is used to generate a new user account.

#### Parameters
- `pswd`: The password for the new account.

#### Usage
```json
{
  "cmd": "genaccount",
  "val": {
    "pswd": "password123"
  }
}
```

#### Possible Errors
- User Already Exists
- Unexpected Error

## Usage

1. **Connect to the Server**:
   - Utilize WebSocket connections to connect clients to the server.

2. **Send Commands**:
   - Send JSON-formatted commands to the server using WebSocket communication.

3. **Handle Responses**:
   - Handle server responses and status messages received via WebSocket.

4. **Error Handling**:
   - Check for status messages in responses to handle errors gracefully.
