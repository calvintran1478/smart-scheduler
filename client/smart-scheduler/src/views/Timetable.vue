<template>
    <ion-page>
      <ion-content class="ion-padding">
        <h1 class="title">Today's Timetable</h1>
        <ion-list>
          <ion-item v-for="(item, index) in scheduleItems" :key="index">
            <ion-label>
              <h2>{{ formatTime(item.start_time) }} - {{ formatTime(item.end_time) }}</h2>
              <p>{{ item.name }} ({{ item.schedule_item_type }})</p>
            </ion-label>
            <ion-button color="danger" @click="deleteFocusSession(item.schedule_item_id)">
              Delete
            </ion-button>
          </ion-item>
        </ion-list>
        <ion-button @click="openModal">Add Focus Session</ion-button>
      <focus-modal v-if="isModalOpen" @close="closeModal">
        <ion-header>
          <ion-toolbar>
            <ion-title>Add Focus Session</ion-title>
            <ion-buttons slot="end">
            </ion-buttons>
          </ion-toolbar>
        </ion-header>
        <ion-content class="ion-padding">
          <ion-list>
            <ion-item>
              <ion-label position="stacked">Session Name</ion-label>
              <ion-input v-model="newFocusSession.name" placeholder="Enter session name"></ion-input>
            </ion-item>
            <ion-item>
              <ion-label position="stacked">Start Time</ion-label>
              <ion-input v-model="newFocusSession.start_time" type="time" required></ion-input>
            </ion-item>
            <ion-item>
              <ion-label position="stacked">End Time</ion-label>
              <ion-input v-model="newFocusSession.end_time" type="time" required></ion-input>
            </ion-item>
          </ion-list>
          <ion-button expand="full" @click="addFocusSession">Add Session</ion-button>
        </ion-content>
      </focus-modal>
      </ion-content>
    </ion-page>
  </template>
  
  <script>
  import {
    IonPage,
    IonContent,
    IonList,
    IonItem,
    IonLabel,
    IonButton,
    IonModal,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonButtons,
    IonInput
  } from "@ionic/vue";
  import { defineComponent } from "vue";
  import { format } from "date-fns";
  import { refreshToken, logout } from "../services/auth";
  
  export default defineComponent({
    components: {
      IonPage,
      IonContent,
      IonList,
      IonItem,
      IonLabel,
      IonButton,
      IonModal,
      IonHeader,
      IonToolbar,
      IonTitle,
      IonButtons,
      IonInput
    },
    data() {
      return {
        scheduleItems: [],
        refreshed: false,
        newFocusSession: {
          name: '',
          start_time: '',
          end_time: '',
        },
        isModalOpen: false
      };
    },
    methods: {
      openModal() {
        this.isModalOpen=true;
      },
      closeModal() {
        this.isModalOpen=false;
      },
      async fetchSchedule() {
        const date = format(new Date(), 'yyyy-MM-dd');
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const token = localStorage.getItem("token");
        if (!token) {
            console.error("No token found");
            return;
        }
        try {
            const response = await fetch(`http://localhost:8000/api/v1/users/schedules/${date}?timezone=${timezone}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            credentials: "include"
            });
          if (response.status === 200) {
            const data = await response.json();
            this.scheduleItems = data.schedule_items;
            console.log(data.schedule_items);
          } else if (response.status == 401) {
            // refresh token
            if (!this.refreshed) {
              await refreshToken();
              this.refreshed = true;
              console.log('Token refresh successful.')
              // try again
              this.fetchSchedule()
            } else {
              console.log('Time out.')
              logout();
            }
          } else {
            console.error('Failed to fetch schedule:', response.statusText);
          }
        } catch (error) {
          console.error('Error fetching schedule:', error);
        }
      },
      formatTime(time) {
        const [hour, minute] = time.split(':');
        const date = new Date();
        date.setHours(hour);
        date.setMinutes(minute);
        return format(date, 'hh:mm a');
      },
    async addFocusSession() {
      const date = format(new Date(), 'yyyy-MM-dd');
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found");
        return;
      }

      const requestBody = {
        name: this.newFocusSession.name,
        start_time: this.newFocusSession.start_time,
        end_time: this.newFocusSession.end_time
      };

      try {
        const response = await fetch(`http://localhost:8000/api/v1/users/schedules/${date}/focus-sessions?timezone=${timezone}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: "include",
          body: JSON.stringify(requestBody)
        });

        if (response.status === 201) {
          const newSession = await response.json();
          this.scheduleItems.push(newSession);
          console.log('Focus session added:', newSession);
          this.closeModal();
        } else if (response.status === 401) {
          console.error('Unauthorized');
        } else if (response.status === 409) {
          console.error('Time conflict with existing schedule');
        } else {
          console.error('Failed to add focus session:', response.statusText);
        }
      } catch (error) {
        console.error('Error adding focus session:', error);
      }
    },
    async deleteFocusSession(id) {
      const date = format(new Date(), 'yyyy-MM-dd');
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found");
        return;
      }

      try {
        const response = await fetch(`http://localhost:8000/api/v1/users/schedules/${date}/focus-sessions/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: "include"
        });

        if (response.status === 204) {
          this.scheduleItems = this.scheduleItems.filter(item => item.schedule_item_id !== id);
          console.log('Focus session deleted:', id);
        } else if (response.status === 401) {
          console.error('Unauthorized');
        } else if (response.status === 404) {
          console.error('Focus session not found');
        } else {
          console.error('Failed to delete focus session:', response.statusText);
        }
      } catch (error) {
        console.error('Error deleting focus session:', error);
      }
    }
    }, 
    mounted() {
      this.fetchSchedule();
    }
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
  ion-button {
    margin: 20px;
  }

  ion-modal {
    --ion-background-color: #ffffff;
  }
  </style>
  