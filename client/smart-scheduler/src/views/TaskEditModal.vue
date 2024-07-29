<template>
    <ion-modal :is-open="true" @didDismiss="closeModal">
      <ion-header>
        <ion-toolbar>
          <ion-title>Edit Task</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeModal">Close</ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content class="ion-padding">
        <ion-item>
          <ion-label position="stacked">Task Name</ion-label>
          <ion-input v-model="name" placeholder="Enter task name"></ion-input>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Due Date</ion-label>
          <ion-datetime display-format="YYYY-MM-DDTHH:mm:ss" v-model="dateTime"></ion-datetime>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Time Estimate</ion-label>
          <ion-item>
            <ion-label>Hours</ion-label>
            <ion-select v-model="timeEstimate.hours">
              <ion-select-option v-for="hour in hours" :key="hour" :value="hour">
                {{ hour }}
              </ion-select-option>
            </ion-select>
          </ion-item>
          <ion-item>
            <ion-label>Minutes</ion-label>
            <ion-select v-model="timeEstimate.minutes">
              <ion-select-option v-for="minute in minutes" :key="minute" :value="minute">
                {{ minute }}
              </ion-select-option>
            </ion-select>
          </ion-item>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Tag</ion-label>
          <ion-select v-model="selectedTag" interface="popover">
            <ion-select-option v-for="tag in tags" :value="tag" :key="tag.name">
              {{ tag.name }}
            </ion-select-option>
          </ion-select>
        </ion-item>
        <ion-button expand="block" @click="updateTask">Update Task</ion-button>
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
    IonSelect,
    IonSelectOption,
  } from "@ionic/vue";
  import { defineComponent, ref, watch } from "vue";
  
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
      IonSelect,
      IonSelectOption,
    },
    props: {
      task: Object,
    },
    setup(props, { emit }) {
      const name = ref(props.task.name);
      const dateTime = ref(`${props.task.deadline.split('T')[0]}T${props.task.deadline.split('T')[1].split('-')[0]}`);
      const timeEstimate = ref({
        hours: props.task.time_estimate.split(':')[0],
        minutes: props.task.time_estimate.split(':')[1],
      });
      const selectedTag = ref(props.task.tag);
      const tags = ref([]);
      const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0"));
      const minutes = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, "0"));
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  
      const fetchTags = async () => {
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("No token found");
          return;
        }
  
        try {
          const response = await fetch("http://localhost:8000/api/v1/users/tags", {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            credentials: "include",
          });
  
          if (response.ok) {
            const data = await response.json();
            tags.value = data.tags;
          } else {
            console.error("Error fetching tags:", response.statusText);
          }
        } catch (error) {
          console.error("Error fetching tags:", error);
        }
      };
  
      const closeModal = () => {
        emit("close");
      };
  
      const updateTask = async () => {
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("No token found");
          return;
        }
  
        const updatedTask = {
          name: name.value,
          deadline: dateTime.value.replace('T', ' '), // format as `YYYY-MM-DD HH:MM:SS`
          time_estimate: `${timeEstimate.value.hours}:${timeEstimate.value.minutes}:00`,
          timezone: timezone.value,
          tag: selectedTag.value ? selectedTag.value.name : null,
        };
  
        try {
          const response = await fetch(`http://localhost:8000/api/v1/users/tasks/${props.task.task_id}`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            credentials: "include",
            body: JSON.stringify(updatedTask),
          });
  
          if (response.ok) {
            emit("task-updated");
            console.log("Update task successful.");
            closeModal();
          } else {
            console.error("Failed to update task:", response.statusText);
          }
        } catch (error) {
          console.error("Error updating task:", error);
        }
      };
  
      fetchTags();
  
      return {
        name,
        dateTime,
        timeEstimate,
        selectedTag,
        tags,
        hours,
        minutes,
        timezone,
        closeModal,
        updateTask,
      };
    },
  });
  </script>
  
  <style scoped>
  /* Add styling later */
  </style>
  