#include <stdio.h>
#include <string.h>


#include "esp_event.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "lwip/err.h"
#include "lwip/sys.h"
#include "nvs_flash.h"
#include "lwip/sockets.h" // Para sockets

//Credenciales de WiFi

#define WIFI_SSID "SSID"
#define WIFI_PASSWORD "PASSOWRD"
#define SERVER_IP     "192.168.0.1" // IP del servidor
#define SERVER_PORT   1234

// Variables de WiFi
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT BIT1
static const char* TAG = "WIFI";
static int s_retry_num = 0;
static EventGroupHandle_t s_wifi_event_group;


void event_handler(void* arg, esp_event_base_t event_base,
                          int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT &&
               event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < 10) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "retry to connect to the AP");
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
        }
        ESP_LOGI(TAG, "connect to the AP fail");
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*)event_data;
        ESP_LOGI(TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

void wifi_init_sta(char* ssid, char* password) {
    s_wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());

    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL, &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL, &instance_got_ip));

    wifi_config_t wifi_config;
    memset(&wifi_config, 0, sizeof(wifi_config_t));

    // Set the specific fields
    strcpy((char*)wifi_config.sta.ssid, WIFI_SSID);
    strcpy((char*)wifi_config.sta.password, WIFI_PASSWORD);
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    wifi_config.sta.pmf_cfg.capable = true;
    wifi_config.sta.pmf_cfg.required = false;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "wifi_init_sta finished.");

    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group,
                                           WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
                                           pdFALSE, pdFALSE, portMAX_DELAY);

    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "connected to ap SSID:%s password:%s", ssid,
                 password);
    } else if (bits & WIFI_FAIL_BIT) {
        ESP_LOGI(TAG, "Failed to connect to SSID:%s, password:%s", ssid,
                 password);
    } else {
        ESP_LOGE(TAG, "UNEXPECTED EVENT");
    }

    ESP_ERROR_CHECK(esp_event_handler_instance_unregister(
        IP_EVENT, IP_EVENT_STA_GOT_IP, instance_got_ip));
    ESP_ERROR_CHECK(esp_event_handler_instance_unregister(
        WIFI_EVENT, ESP_EVENT_ANY_ID, instance_any_id));
    vEventGroupDelete(s_wifi_event_group);
}

void nvs_init() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
}

char* create_packet_0() {
    // Get MAC Adress
    char* mac = "0";
    // Random id
    char* id = "0";
    // Header
    char* header = strcat(mac, id);
    // Header + Protocol + Transport + Length
    header = strcat(header, "0016");
    // Done
    
    // Body
    // timestamp
    char* body = "0000";

    //Join message
    char* packet = strcat(header, body);
    return packet;
}

char* create_packet_1() {
    // Get MAC Adress
    char* mac = "0";
    // Random id
    char* id = "0";
    // Header
    char* header = strcat(mac, id);
    // Header + Protocol + Transport + Length
    header = strcat(header, "0017");
    // Done
    
    // Body
    // timestamp
    char* body = "0000";
    // batt level
    body = strcat(body, "0");

    //Join message
    char* packet = strcat(header, body);
    return packet;

}

char* create_packet_2() {
    // Get MAC Adress
    char* mac = "0";
    // Random id
    char* id = "0";
    // Header
    char* header = strcat(mac, id);
    // Header + Protocol + Transport + Length
    char* header = strcat(header, "0027");
    // Done
    
    // Body
    // timestamp
    char* body = "0000";
    // batt level
    body = strcat(body, "0");
    // temp
    body = strcat(body, "0");
    // press
    body = strcat(body, "0");
    // hum
    body = strcat(body, "0");
    // co
    body = strcat(body, "0");

    //Join message
    char* packet = strcat(header, body);
    return packet;

}

//TBD
char* create_packet_3() {}

//TBD
char* create_packet_4() {}


int socket_tcp(){
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr.s_addr);

    // Crear un socket
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Error al crear el socket");
        return;
    }

    // Conectar al servidor
    if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) != 0) {
        ESP_LOGE(TAG, "Error al conectar");
        close(sock);
        return;
    }

    return sock;
}

void close_tcp(socket) {
    // Cerrar el socket
    close(sock);
}

char* config_conn(socket) {
    // Pedir protocolo
    char* config = "CONFIG";
    send(socket, config, strlen(config), 0);

    // Recibir respuesta
    char rx_buffer[128];
    int rx_len = recv(socket, rx_buffer, sizeof(rx_buffer) - 1, 0);
    if (rx_len < 0) {
        ESP_LOGE(TAG, "Error al recibir datos");
        return;
    }
    ESP_LOGI(TAG, "Datos recibidos: %s", rx_buffer);

    return rx_buffer;
}

void send_data(socket, conf_data) {
    char* send_ack = "PACKAGE";
    send(socket, send_ack, strlen(send_ack), 0);
    // Chequeo de protocolo (y capa de transporte a futuro), para luego enviar datos
    if (strcmp(conf_data, "00") == 0) {
        ESP_LOGI(TAG,"Usando protocolo 0\n");
        // protocolo 0
        char* pack = create_packet_0();
        ESP_LOGI(TAG, "Paquete a enviar: %s", pack);
        send(socket, pack, strlen(pack), 0);
        
    }
    else if (strcmp(conf_data, "10") == 0) {
        ESP_LOGI(TAG,"Usando protocolo 1\n");
        // protocolo 1
        char* pack = create_packet_1();
        ESP_LOGI(TAG, "Paquete a enviar: %s", pack);
        send(socket, pack, strlen(pack), 0);
    }
    else if (strcmp(conf_data, "20") == 0) {
        ESP_LOGI(TAG,"Usando protocolo 2\n");
        // protocolo 2
        char* pack = create_packet_2();
        ESP_LOGI(TAG, "Paquete a enviar: %s", pack);
        send(socket, pack, strlen(pack), 0);
        
    }
    else if (strcmp(conf_data, "30") == 0) {
        ESP_LOGI(TAG,"Usando protocolo 3\n");
        // protocolo 3
        char* pack = create_packet_3();
        ESP_LOGI(TAG, "Paquete a enviar: %s", pack);
        send(socket, pack, strlen(pack), 0);
    }
    else if (strcmp(conf_data, "40") == 0) {
        ESP_LOGI(TAG,"Usando protocolo 4\n");
        // protocolo 4
        char* pack = create_packet_4();
        ESP_LOGI(TAG, "Paquete a enviar: %s", pack);
        send(socket, pack, strlen(pack), 0);
    }
    else {
        //error
        ESP_LOGI(TAG,"Mensaje invalido\n");
    }
    close_tcp(socket);
}


void app_main(void){
    //añadir loop de SLEEP
    nvs_init();
    wifi_init_sta(WIFI_SSID, WIFI_PASSWORD);
    ESP_LOGI(TAG,"Conectado a WiFi!\n");
    int sock = socket_tcp();
    ESP_LOGI(TAG,"Conectado al socket\n");
    char* conf_data = config_conn(sock);
    ESP_LOGI(TAG,"Configuracion lista, enviando datos\n");
    send_data(sock, conf_data);
    ESP_LOGI(TAG,"A mimir\n");
    //Deep Sleep for one second
    esp_deep_sleep(1000000);
}
