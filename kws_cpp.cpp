#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <thread>
#include <chrono>
#include <ctime>
#include <random>
#include <filesystem>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

struct Contact {
    std::string username;
    std::string auth_id;
    std::string last_contact;
    std::string user_defined_name;
    std::string ip_address;
    std::string status;
};

const int SERVER_PORT = 5000;
int PING_INTERVAL = 30;

const std::string AUTH_KEY_FILE = "auth.key";
const std::string CONFIG_FILE = "config.cfk";
const std::string CONTACT_FILE = "contaktd.cdf";
const std::string DATATRANS_FILE = "datatrans.ksys";
const std::string DATA_FILE = "data.ksys";

std::string current_timestamp() {
    std::time_t t = std::time(nullptr);
    char buf[64];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&t));
    return buf;
}

void log_message(const std::string& msg) {
    std::ofstream f(DATATRANS_FILE, std::ios::app);
    f << "[" << current_timestamp() << "] " << msg << "\n";
}

void log_permanent(const std::string& msg) {
    std::ofstream f(DATA_FILE, std::ios::app);
    f << "[" << current_timestamp() << "] " << msg << "\n";
}

std::string generate_uuid() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<uint32_t> dis(0, 0xFFFFFFFF);
    std::stringstream ss;
    ss << std::hex;
    ss << dis(gen) << dis(gen) << dis(gen) << dis(gen);
    return ss.str();
}

std::string create_required_files() {
    std::string auth_key;
    if (!std::filesystem::exists(AUTH_KEY_FILE)) {
        auth_key = generate_uuid();
        std::ofstream f(AUTH_KEY_FILE);
        f << auth_key;
        std::cout << "Neuer Auth-Key erstellt: " << auth_key << std::endl;
    } else {
        std::ifstream f(AUTH_KEY_FILE);
        std::getline(f, auth_key);
        std::cout << "Auth-Key geladen: " << auth_key << std::endl;
    }
    if (!std::filesystem::exists(CONFIG_FILE)) {
        std::ofstream f(CONFIG_FILE);
        f << "username=default_user\n";
        f << "ping_interval=" << PING_INTERVAL << "\n";
        std::cout << "Standard-Konfiguration erstellt." << std::endl;
    }
    if (!std::filesystem::exists(CONTACT_FILE)) {
        std::ofstream(CONTACT_FILE);
        std::cout << "Kontaktdatei erstellt." << std::endl;
    }
    if (!std::filesystem::exists(DATATRANS_FILE)) {
        std::ofstream(DATATRANS_FILE);
    }
    if (!std::filesystem::exists(DATA_FILE)) {
        std::ofstream(DATA_FILE);
    }
    return auth_key;
}

std::vector<Contact> load_contacts() {
    std::vector<Contact> contacts;
    std::ifstream f(CONTACT_FILE);
    std::string line;
    while (std::getline(f, line)) {
        if (line.empty()) continue;
        if (line.back() == '|') line.pop_back();
        std::stringstream ss(line);
        std::string part; std::vector<std::string> parts;
        while (std::getline(ss, part, ';')) parts.push_back(part);
        if (parts.size() >= 6) {
            contacts.push_back({parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]});
        }
    }
    return contacts;
}

void save_contacts(const std::vector<Contact>& contacts) {
    std::ofstream f(CONTACT_FILE);
    for (const auto& c : contacts) {
        f << c.username << ';' << c.auth_id << ';' << c.last_contact << ';'
          << c.user_defined_name << ';' << c.ip_address << ';' << c.status << "|\n";
    }
}

std::vector<Contact> parse_contacts_from_string(const std::string& data) {
    std::vector<Contact> contacts;
    std::stringstream stream(data);
    std::string line;
    while (std::getline(stream, line)) {
        if (line.empty()) continue;
        if (line.back() == '|') line.pop_back();
        std::stringstream ss(line);
        std::string part; std::vector<std::string> parts;
        while (std::getline(ss, part, ';')) parts.push_back(part);
        if (parts.size() >= 6) {
            contacts.push_back({parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]});
        }
    }
    return contacts;
}

void merge_contacts(std::vector<Contact>& existing, const std::vector<Contact>& add) {
    for (const auto& nc : add) {
        bool found = false;
        for (auto& c : existing) {
            if (c.auth_id == nc.auth_id) {
                found = true;
                if (nc.last_contact > c.last_contact) {
                    c.last_contact = nc.last_contact;
                }
                break;
            }
        }
        if (!found) existing.push_back(nc);
    }
}

void handle_client(int client, const std::string& auth_key) {
    char buffer[4096];
    ssize_t n = recv(client, buffer, sizeof(buffer)-1, 0);
    if (n <= 0) { close(client); return; }
    buffer[n] = '\0';
    std::string data(buffer);
    std::stringstream ss(data);
    std::string part; std::vector<std::string> parts;
    while (std::getline(ss, part, ';')) parts.push_back(part);

    if (parts.empty()) { close(client); return; }

    if (parts[0] == "PING") {
        std::string sender = parts.size() > 1 ? parts[1] : "unknown";
        std::cout << "PING von " << sender << std::endl;
        send(client, "PONG", 4, 0);
        log_message("PING von " + sender);
    } else if (parts[0] == "MSG") {
        if (parts.size() >= 4) {
            std::string sender = parts[1];
            std::string msg_time = parts[2];
            std::string message = data.substr(data.find(parts[3]));
            std::cout << "MSG von " << sender << ": " << message << std::endl;
            log_message("MSG von " + sender + ": " + message);
            send(client, "MSG_RECEIVED", 12, 0);
        }
    } else if (parts[0] == "REQ") {
        if (parts.size() >= 4) {
            std::string sender_auth = parts[1];
            std::string target_auth = parts[2];
            std::string command = parts[3];
            std::string payload = data.substr(data.find(command) + command.size() + 1);
            if (target_auth != auth_key) {
                send(client, "WRONG_TARGET", 12, 0);
            } else if (command == "INFO") {
                std::string resp = "INFO;" + auth_key;
                send(client, resp.c_str(), resp.size(), 0);
            } else if (command == "ADDLIST") {
                auto new_contacts = parse_contacts_from_string(payload);
                auto existing = load_contacts();
                merge_contacts(existing, new_contacts);
                save_contacts(existing);
                send(client, "ADDLIST_RECEIVED", 16, 0);
            } else if (command == "LIST") {
                std::ifstream f(CONTACT_FILE);
                std::stringstream out; out << f.rdbuf();
                std::string contacts = out.str();
                std::string resp = "LIST;" + contacts;
                send(client, resp.c_str(), resp.size(), 0);
            } else {
                send(client, "UNBEKANNT_COMMAND", 18, 0);
            }
        } else {
            send(client, "INVALID_REQ_FORMAT", 19, 0);
        }
    } else {
        send(client, "UNKNOWN_COMMAND", 15, 0);
    }
    close(client);
}

void server_loop(const std::string& auth_key) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(SERVER_PORT);
    bind(server_fd, (sockaddr*)&addr, sizeof(addr));
    listen(server_fd, 5);
    std::cout << "Server läuft auf Port " << SERVER_PORT << std::endl;
    while (true) {
        int client = accept(server_fd, nullptr, nullptr);
        std::thread(handle_client, client, auth_key).detach();
    }
}

void ping_contacts(const std::string& auth_key) {
    while (true) {
        auto contacts = load_contacts();
        bool updated = false;
        for (auto& c : contacts) {
            int s = socket(AF_INET, SOCK_STREAM, 0);
            sockaddr_in addr{};
            addr.sin_family = AF_INET;
            inet_pton(AF_INET, c.ip_address.c_str(), &addr.sin_addr);
            addr.sin_port = htons(SERVER_PORT);
            struct timeval tv; tv.tv_sec = 5; tv.tv_usec = 0;
            setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
            setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
            if (connect(s, (sockaddr*)&addr, sizeof(addr)) == 0) {
                std::string msg = "PING;" + auth_key;
                send(s, msg.c_str(), msg.size(), 0);
                char buf[16];
                int n = recv(s, buf, sizeof(buf)-1, 0);
                if (n > 0) {
                    buf[n] = '\0';
                    if (std::string(buf) == "PONG") {
                        c.status = "online";
                        c.last_contact = current_timestamp();
                        updated = true;
                    }
                }
            } else {
                c.status = "offline";
                updated = true;
            }
            close(s);
        }
        if (updated) save_contacts(contacts);
        std::this_thread::sleep_for(std::chrono::seconds(PING_INTERVAL));
    }
}

int main() {
    std::string auth_key = create_required_files();
    std::ifstream cf(CONFIG_FILE);
    std::string line;
    while (std::getline(cf, line)) {
        auto pos = line.find('=');
        if (pos == std::string::npos) continue;
        std::string key = line.substr(0, pos);
        std::string val = line.substr(pos+1);
        if (key == "ping_interval") {
            try { PING_INTERVAL = std::stoi(val); } catch(...) {}
        }
    }
    std::thread(server_loop, auth_key).detach();
    std::thread(ping_contacts, auth_key).detach();
    std::cout << "kws_cpp läuft. STRG+C zum Beenden." << std::endl;
    while (true) std::this_thread::sleep_for(std::chrono::seconds(1));
    return 0;
}

