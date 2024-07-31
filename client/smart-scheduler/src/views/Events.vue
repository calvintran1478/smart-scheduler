<template>
    <ion-page>
      <ion-content class="ion-padding">
        <h1 class="title">Upcoming Events</h1>
        <ion-list>
          <ion-item v-for="event in events" :key="event.event_id">
            <ion-label>
              <h2>{{ event.summary }}</h2>
              <p>
                Start: {{ event.start_time.split("T")[0] }} at
                {{ event.start_time.split("T")[1].split("-")[0] }}
              </p>
              <p>
                End: {{ event.end_time.split("T")[0] }} at
                {{ event.end_time.split("T")[1].split("-")[0] }}
              </p>
              <p v-if="event.location">Location: {{ event.location }}</p>
              <p v-if="event.description">Description: {{ event.description }}</p>
              <p>Repeat: {{ event.repeat_rule }}</p>
            </ion-label>
            <ion-button slot="end" @click="editEvent(event)">Edit</ion-button>
            <ion-button slot="end" color="danger" @click="deleteEvent(event)"
              >Delete</ion-button
            >
          </ion-item>
        </ion-list>
        <ion-fab vertical="bottom" horizontal="end" slot="fixed">
          <ion-fab-button @click="openModal">
            <ion-icon :icon="addOutline"></ion-icon>
          </ion-fab-button>
        </ion-fab>
        <event-modal
          v-if="isModalOpen"
          @close="closeModal"
          @event-created="addEvent"
        ></event-modal>
        <event-edit-modal
          v-if="isEditModalOpen"
          :event="selectedEvent"
          @close="closeEditModal"
        />
        <ion-alert
          v-if="isDeleteAlertOpen"
          header="Confirm Delete"
          message="Are you sure you want to delete this event?"
          :buttons="[
            {
              text: 'Cancel',
              role: 'cancel',
              handler: () => {
                isDeleteAlertOpen.value = false;
              },
            },
            {
              text: 'Delete',
              role: 'destructive',
              handler: deleteConfirmedEvent,
            },
          ]"
        />
      </ion-content>
    </ion-page>
  </template>
  
  <script>
  import {
    IonContent,
    IonHeader,
    IonPage,
    IonToolbar,
    IonTitle,
    IonList,
    IonItem,
    IonLabel,
    IonFab,
    IonFabButton,
    IonIcon,
    IonButton,
    IonAlert,
  } from "@ionic/vue";
  import { defineComponent, ref, onMounted } from "vue";
  import { addOutline } from "ionicons/icons";
  import EventModal from "./EventModal.vue";
  import EventEditModal from "./EventEditModal.vue";
  import { refreshToken, logout } from "../services/auth";
  
  export default defineComponent({
    components: {
      IonContent,
      IonHeader,
      IonPage,
      IonToolbar,
      IonTitle,
      IonList,
      IonItem,
      IonLabel,
      IonFab,
      IonFabButton,
      IonIcon,
      EventModal,
      EventEditModal,
      IonButton,
      IonAlert,
    },
    setup() {
      const events = ref([]);
      const isModalOpen = ref(false);
      const isEditModalOpen = ref(false);
      const isDeleteAlertOpen = ref(false);
      const selectedEvent = ref(null);
      const eventToDelete = ref(null);
      const refreshed = ref(false);
  
      const openModal = () => {
        isModalOpen.value = true;
      };
  
      const closeModal = () => {
        isModalOpen.value = false;
      };
  
      const addEvent = (event) => {
        if (Array.isArray(events.value)) {
          events.value.push(event);
        } else {
          events.value = [event];
        }
      };
  
      const editEvent = (event) => {
        selectedEvent.value = event;
        isEditModalOpen.value = true;
      };
  
      const deleteEvent = (event) => {
        eventToDelete.value = event;
        isDeleteAlertOpen.value = true;
      };
  
      const deleteConfirmedEvent = async () => {
        const event = eventToDelete.value;
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("No token found");
          return;
        }
        try {
          const response = await fetch(
            `http://localhost:8000/api/v1/users/events/${event.event_id}?start=${event.start_time.replace(/[:-]/g, "-").replace("T", "-").slice(0, 16)}&timezone=${event.timezone}`,
            {
              method: "DELETE",
              headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
              },
              credentials: "include",
            }
          );
          if (response.status === 204) {
            events.value = events.value.filter((e) => e.event_id !== event.event_id);
            isDeleteAlertOpen.value = false;
            console.log('Delete event successful.')
          } else if (response.status == 401) {
              // refresh token
              if (!refreshed.value) {
                await refreshToken();
                refreshed.value = true;
                console.log('Token refresh successful.')
                // try again
                this.deleteConfirmedEvent()
              } else {
                console.log('Time out.')
                logout();
              }
            } else {
            console.error("Failed to delete event:", response.statusText);
          }
        } catch (error) {
          console.error("Error deleting event:", error);
        }
      };
  
      const closeEditModal = () => {
        isEditModalOpen.value = false;
        fetchEvents();
      };
  
      const fetchEvents = async () => {
        const token = localStorage.getItem("token"); 
        if (!token) {
          console.error("No token found");
          return;
        }
        
        try {
          const startDate = new Date().toISOString().slice(0, 16).replace(/[:-]/g, "-");
          const endDate = new Date(Date.now() + 30*24*60*60*1000).toISOString().slice(0, 16).replace(/[:-]/g, "-");
          const response = await fetch(`http://localhost:8000/api/v1/users/events?start=${startDate}&end=${endDate}&timezone=${Intl.DateTimeFormat().resolvedOptions().timeZone}`, {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            credentials: "include",
          });
          
          if (response.ok) {
            const data = await response.json();
            events.value = data.events;
            console.log("Fetch events successful.");
            console.log(events.value);
          } else if (response.status == 401) {
              // refresh token
              if (!refreshed.value) {
                await refreshToken();
                refreshed.value = true;
                console.log('Token refresh successful.')
                // try again
                this.fetchEvents()
              } else {
                console.log('Time out.')
                logout();
              }
            } else {
            console.error("Failed to fetch events: ", response.status, response.statusText);
          }
        } catch (err) {
          console.error("Failed to fetch events:", err);
        }
      };
  
      onMounted(() => {
        fetchEvents();
      });
  
      return {
        events,
        isModalOpen,
        isEditModalOpen,
        isDeleteAlertOpen,
        selectedEvent,
        eventToDelete,
        openModal,
        closeModal,
        addEvent,
        editEvent,
        closeEditModal,
        deleteEvent,
        deleteConfirmedEvent,
        addOutline,
      };
    },
  });
  </script>
  
  <style scoped>
  .title {
    padding-top: 30px;
    font-size: 28px;
    font-weight: bold;
    text-align: left;
    padding-left: 25px;
  }
  </style>
  