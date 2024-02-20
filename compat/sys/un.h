
// For miniupnpc

#define UNIX_PATH_LEN   108
struct sockaddr_un {
	uint16_t sun_family;
	char     sun_path[UNIX_PATH_LEN];
};
