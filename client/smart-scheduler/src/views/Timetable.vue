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
          </ion-item>
        </ion-list>
      </ion-content>
    </ion-page>
  </template>
  
  <script>
  import {
    IonPage,
    IonContent,
    IonList,
    IonItem,
    IonLabel
  } from "@ionic/vue";
  import { defineComponent } from "vue";
  import { format } from "date-fns";
  
  export default defineComponent({
    components: {
      IonPage,
      IonContent,
      IonList,
      IonItem,
      IonLabel,
    },
    data() {
      return {
        scheduleItems: [],
      };
    },
    methods: {
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
  </style>
  