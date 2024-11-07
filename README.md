# kanboardizer

**Kanboardizer** is a simple Home Assistant custom component that loads from a Kanboard installation the informations about:

- Number of users
- Number of project (active, closed and total)
- Number of overall tasks (active, closed and total)
- Number of overdue tasks

by interrogating the Kanboard APIs.

##setup

Simply download the content of the `kanboardizer` directory and place under your `custom_components` directory of Home Assistant.
Then edit your `configuration.yaml` by adding the Kanboardizer section:

	kanboardizer:
	api_url: "https://<kanboard_server>/jsonrpc.php"
	api_token: "<api_token>"
	user: "<user_name>"

The API token could be copied from the _Settings_ section of your user.

Then restart your Home Assistant instance.