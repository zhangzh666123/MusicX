// hooks/useEnvironment.js
export function useEnvironment() {
    const envData = reactive({ city: '', weather: '', type: '' });
  
    const fetchEnv = () => {
      AMap.plugin(['AMap.CitySearch', 'AMap.Weather'], () => {
        const citySearch = new AMap.CitySearch();
        citySearch.getLocalCity((status, result) => {
          if (status === 'complete') {
            const city = result.city;
            const weather = new AMap.Weather();
            weather.getLive(city, (err, data) => {
              envData.city = city;
              envData.weather = data.weather;
              // 此时已完成环境捕获，可以触发后续的逻辑链
            });
          }
        });
      });
    };
  
    return { envData, fetchEnv };
  }