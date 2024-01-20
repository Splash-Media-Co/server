<p align="center">
  <img src="https://github.com/Splash-Media-Co/server/assets/103071021/8baf6086-d31a-4404-be8a-07c6fc0aed1f)https://github.com/Splash-Media-Co/server/assets/103071021/8baf6086-d31a-4404-be8a-07c6fc0aed1f"/>
</p>

<h1 align="center">Backend server for Splash</h1>
<h4 align="center">This is the server that runs all of Splash.</h4>

---

# Splash Server Documentation

## Overview

The Splash server is responsible for handling various commands from clients, such as posting messages, authentication, retrieving posts, and account creation. This document provides documentation for the supported commands and their payloads.

## Commands

### 1. `direct`

#### Payload
```json
{"cmd": "direct", "val": {"cmd": "post", "val": {"type": "send", "p": "Your post content", "attachment": "Optional attachment"}}}
```

- **Description**: Direct command for posting messages.
- **Parameters**:
  - `"type"`: Specifies the type of post, currently supporting `"send"` for sending messages.
  - `"p"`: The content of the post.
  - `"attachment"`: Optional attachment for the post (e.g., an image).

#### Payload
```json
{"cmd": "direct", "val": {"cmd": "post", "val": {"type": "delete", "uid": "PostUID"}}}
```

- **Description**: Direct command for deleting a post.
- **Parameters**:
  - `"type"`: Specifies the type of post operation, currently supporting `"delete"`.
  - `"uid"`: Unique identifier for the post to be deleted.

#### Payload
```json
{"cmd": "direct", "val": {"cmd": "post", "val": {"type": "edit", "uid": "PostUID", "edit": "Edited post content"}}}
```

- **Description**: Direct command for editing a post.
- **Parameters**:
  - `"type"`: Specifies the type of post operation, currently supporting `"edit"`.
  - `"uid"`: Unique identifier for the post to be edited.
  - `"edit"`: The new content of the post.

### 2. `auth`

#### Payload
```json
{"cmd": "auth", "val": {"pswd": "YourPassword"}}
```

- **Description**: Authenticate a user.
- **Parameters**:
  - (Username set using CloudLink usernames)
  - `"pswd"`: User's password.

### 3. `retrieve`

#### Payload
```json
{"cmd": "retrieve", "val": {"type": "latest", "c": "ChatID", "o": "Offset"}}
```

- **Description**: Retrieve posts.
- **Parameters**:
  - `"type"`: Specifies the retrieval type, currently supporting `"latest"`.
  - `"c"`: Chat ID for posts retrieval.
  - `"o"`: Offset for retrieving posts.

### 4. `genaccount`

#### Payload
```json
{"cmd": "genaccount", "val": {"pswd": "NewPassword"}}
```

- **Description**: Generate a new user account.
- **Parameters**:
  - (Username set using CloudLink usernames)
  - `"pswd"`: New user's password.

## Error Handling

The server handles various errors and sends corresponding status messages back to the clients.

- **Not Authenticated**:
  - Status message: `"Not authenticated"`
  - Action logged: `"post_fail"`, `"delete_fail"`, `"edit_fail"`, or `"retrieve_fail"`.

- **Invalid Password**:
  - Status message: `"Invalid password"`
  - Action logged: `"auth_fail"`.

- **User Doesn't Exist**:
  - Status message: `"User doesn't exist"`
  - Action logged: `"auth_fail"`.

- **User Already Exists**:
  - Status message: `"User already exists"`
  - Action logged: `"create_account_fail"`.

- **Post Not Found**:
  - Status message: `"Post not found"`
  - Action logged: `"delete_fail"`.

- **Not Authorized**:
  - Status message: `"Not authorized"`
  - Action logged: `"delete_fail"` or `"edit_fail"`.

- **Unexpected Error**:
  - Status message: `"An unexpected error occurred."`
  - Action logged: `"create_account_fail"`.

## Usage

1. **Connect to the Server**:
   - Use the `on_connect` event to handle client connections.
   - Use the `on_disconnect` event to handle client disconnections.

2. **Send Commands**:
   - Use the `direct` command to post messages.
   - Use the `auth` command to authenticate users.
   - Use the `retrieve` command to retrieve posts.
   - Use the `genaccount` command to generate new user accounts.

3. **Handle Responses**:
   - Utilize the `on_message` event to handle server responses.
   - Check the status messages for success or failure.

4. **Error Handling**:
   - Pay attention to status messages for error handling.
   - Refer to the specific error conditions mentioned in the documentation.

5. **Logging**:
   - The server logs various actions and errors using the OceanAuditLogger.
   - Monitor logs for debugging and tracking user actions.

6. **Graceful Termination**:
   - The server can be terminated gracefully using `CTRL+C`.
   - Logs are closed, and the system exits gracefully.

7. **Start the Server**:
   - Ensure that the server is started using the `server.run()` command.
