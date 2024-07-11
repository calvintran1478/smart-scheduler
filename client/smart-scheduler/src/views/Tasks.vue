<template>
    <ion-page>
      <ion-content class="ion-padding">
        <h1 class="title">Tasks to get done</h1>
        <ion-list>
          <ion-item v-for="task in tasks" :key="task.task_id">
            <ion-label>
              <h2>{{ task.name }}</h2>
              <p>Due: {{ task.deadline_date }} at {{ task.deadline_time }}</p>
              <p v-if="task.tag">Tag: {{ task.tag.name }} <span :style="{color: task.tag.colour}">●</span></p>
            </ion-label>
          </ion-item>
        </ion-list>
        <ion-fab vertical="bottom" horizontal="end" slot="fixed">
          <ion-fab-button @click="openModal">
            <ion-icon :icon="addOutline"></ion-icon>
          </ion-fab-button>
        </ion-fab>
        <task-modal v-if="isModalOpen" @close="closeModal" @task-created="addTask"></task-modal>
      </ion-content>
    </ion-page>
  </template>
  
  <script>
  import { IonContent, IonHeader, IonPage, IonToolbar, IonTitle, IonList, IonItem, IonLabel, IonFab, IonFabButton, IonIcon } from "@ionic/vue";
  import { defineComponent, ref, onMounted } from "vue";
  import { addOutline } from "ionicons/icons";
  import TaskModal from "./TaskModal.vue";
  
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
      TaskModal
    },
    setup() {
      const tasks = ref([]);
      const isModalOpen = ref(false);
  
      const openModal = () => {
        isModalOpen.value = true;
      };
  
      const closeModal = () => {
        isModalOpen.value = false;
      };
  
      const addTask = (task) => {
        tasks.value.push(task);
      };
  
      const fetchTasks = async () => {
        const token = localStorage.getItem("token"); // Retrieve token from localStorage
        if (!token) {
          console.error("No token found");
          return;
        }
        console.log(token);
        try {
          const response = await fetch('http://localhost:8000/api/v1/users/tasks', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              "Authorization": `Bearer ${token}`
            }
          });
          if (response.ok) {
            const data = await response.json();
            tasks.value = data.tasks;
          } else {
            console.error('Failed to fetch tasks:', response.statusText);
          }
        } catch (error) {
          console.error('Error fetching tasks:', error);
        }
      };
  
      onMounted(() => {
        fetchTasks();
      });
  
      return {
        tasks,
        isModalOpen,
        openModal,
        closeModal,
        addTask,
        addOutline
      };
    }
  });
  </script>
  
  <style scoped>
  /* styling later */
    .title {
        padding-top: 30px;
        font-size: 28px;
        font-weight: bold;
        text-align: left;
        padding-left: 25px;
    }
  </style>
  