/**
 * relay_registration.h - Helper for relay nodes to register with directory
 */

#ifndef RELAY_REGISTRATION_H
#define RELAY_REGISTRATION_H

/**
 * Register this relay with the directory server
 *
 * @param dir_host Directory server hostname
 * @param dir_port Directory server port (typically 5000)
 * @param relay_port This relay's listening port
 * @param relay_type Node type: 1=guard, 2=middle, 3=exit
 * @return 0 on success, -1 on failure
 */
int register_with_directory(const char *dir_host, int dir_port, int relay_port, int relay_type);

#endif /* RELAY_REGISTRATION_H */
