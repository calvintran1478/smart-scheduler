<template>
    <ion-modal :is-open="true" @didDismiss="closeModal">
      <ion-header>
        <ion-toolbar>
          <ion-title>Edit Event</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeModal">Close</ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content class="ion-padding">
        <ion-item>
          <ion-label position="stacked">Summary</ion-label>
          <ion-input v-model="summary" placeholder="Enter event summary"></ion-input>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Start Time</ion-label>
          <ion-datetime display-format="YYYY-MM-DDTHH:mm" v-model="startTime"></ion-datetime>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">End Time</ion-label>
          <ion-datetime display-format="YYYY-MM-DDTHH:mm" v-model="endTime"></ion-datetime>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Description</ion-label>
          <ion-textarea v-model="description" placeholder="Enter event description"></ion-textarea>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Location</ion-label>
          <ion-input v-model="location" placeholder="Enter event location"></ion-input>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Repeat Rule</ion-label>
          <ion-select v-model="repeatRule" placeholder="Select repeat rule">
            <ion-select-option value="none">None</ion-select-option>
            <ion-select-option value="daily">Daily</ion-select-option>
            <ion-select-option value="weekly">Weekly</ion-select-option>
            <ion-select-option value="monthly">Monthly</ion-select-option>
            <ion-select-option value="yearly">Yearly</ion-select-option>
          </ion-select>
        </ion-item>
        <ion-button expand="block" @click="updateEvent">Update Event</ion-button>
      </ion-content>
    </ion-modal>
  </template>
  
  <script>
  import {
    IonModal,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonButtons,
    IonButton,
    IonContent,
    IonItem,
    IonLabel,
    IonInput,
    IonDatetime,
    IonTextarea,
    IonSelect,
    IonSelectOption,
  } from "@ionic/vue";
  import { defineComponent, ref, watch } from "vue";
  import { refreshToken, logout } from "../services/auth";
  
  export default defineComponent({
    components: {
      IonModal,
      IonHeader,
      IonToolbar,
      IonTitle,
      IonButtons,
      IonButton,
      IonContent,
      IonItem,
      IonLabel,
      IonInput,
      IonDatetime,
      IonTextarea,
      IonSelect,
      IonSelectOption,
    },
    props: {
      event: Object,
    },
    emits: ["close", "event-updated"],
    setup(props, { emit }) {
      const summary = ref(props.event.summary);
      const startTime = ref(props.event.start_time);
      const endTime = ref(props.event.end_time);
      const description = ref(props.event.description);
      const location = ref(props.event.location);
      const repeatRule = ref(props.event.repeat_rule);
      const refreshed = ref(false);
  
      watch(
        () => props.event,
        (newEvent) => {
          summary.value = newEvent.summary;
          startTime.value = newEvent.start_time;
          endTime.value = newEvent.end_time;
          description.value = newEvent.description;
          location.value = newEvent.location;
          repeatRule.value = newEvent.repeat_rule;
        }
      );
  
      const closeModal = () => {
        emit("close");
      };
  
      const updateEvent = async () => {
        const updatedEvent = {
          summary: summary.value,
          start_time: startTime.value,
          end_time: endTime.value,
          description: description.value,
          location: location.value,
          repeat_rule: repeatRule.value,
        };
  
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("No token found");
          return;
        }
  
        try {
          const response = await fetch(
            `http://localhost:8000/api/v1/users/events/${props.event.event_id}`,
            {
              method: "PUT",
              headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
              },
              credentials: "include",
              body: JSON.stringify(updatedEvent),
            }
          );
  
          if (response.ok) {
            const data = await response.json();
            emit("event-updated", data.event);
            closeModal();
            console.log('Edit event successful.')
          } else if (response.status == 401) {
              // refresh token
              if (!refreshed.value) {
                await refreshToken();
                refreshed.value = true;
                console.log('Token refresh successful.')
                // try again
                this.updateEvent()
              } else {
                console.log('Time out.')
                logout();
              }
            } else {
            console.error("Failed to update event:", response.statusText);
          }
        } catch (error) {
          console.error("Error updating event:", error);
        }
      };
  
      return {
        summary,
        startTime,
        endTime,
        description,
        location,
        repeatRule,
        closeModal,
        updateEvent,
      };
    },
  });
  </script>
  
  <style scoped>
  ion-item {
    margin-bottom: 20px;
  }
  </style>
  