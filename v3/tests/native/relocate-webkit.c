/* Test-only relocation of SDK subprocess executables.
 * Does not intercept file operations, IPC, or application behavior.
 * Installed applications use their distribution's normal WebKit paths.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <limits.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static const char *relocate(const char *path, char *buffer) {
    const char *prefix = "/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/";
    const char *directory = getenv("EFFILIFE_TEST_WEBKIT_DIR");
    if (!directory || strncmp(path, prefix, strlen(prefix)) != 0) return path;
    const char *name = path + strlen(prefix);
    if (strcmp(name, "WebKitWebProcess") && strcmp(name, "WebKitNetworkProcess") && strcmp(name, "WebKitGPUProcess")) return path;
    int length = snprintf(buffer, PATH_MAX, "%s/%s", directory, name);
    return length > 0 && length < PATH_MAX ? buffer : path;
}

int execve(const char *path, char *const argv[], char *const envp[]) {
    int (*original)(const char *, char *const[], char *const[]) = dlsym(RTLD_NEXT, "execve");
    char buffer[PATH_MAX];
    return original(relocate(path, buffer), argv, envp);
}

int execv(const char *path, char *const argv[]) {
    int (*original)(const char *, char *const[]) = dlsym(RTLD_NEXT, "execv");
    char buffer[PATH_MAX];
    return original(relocate(path, buffer), argv);
}

int execvp(const char *path, char *const argv[]) {
    int (*original)(const char *, char *const[]) = dlsym(RTLD_NEXT, "execvp");
    char buffer[PATH_MAX];
    return original(relocate(path, buffer), argv);
}

int posix_spawn(pid_t *pid, const char *path, const posix_spawn_file_actions_t *actions, const posix_spawnattr_t *attributes, char *const argv[], char *const envp[]) {
    int (*original)(pid_t *, const char *, const posix_spawn_file_actions_t *, const posix_spawnattr_t *, char *const[], char *const[]) = dlsym(RTLD_NEXT, "posix_spawn");
    char buffer[PATH_MAX];
    return original(pid, relocate(path, buffer), actions, attributes, argv, envp);
}

int posix_spawnp(pid_t *pid, const char *path, const posix_spawn_file_actions_t *actions, const posix_spawnattr_t *attributes, char *const argv[], char *const envp[]) {
    int (*original)(pid_t *, const char *, const posix_spawn_file_actions_t *, const posix_spawnattr_t *, char *const[], char *const[]) = dlsym(RTLD_NEXT, "posix_spawnp");
    char buffer[PATH_MAX];
    return original(pid, relocate(path, buffer), actions, attributes, argv, envp);
}
